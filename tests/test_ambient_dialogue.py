import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from ambient_dialogue import exchange
from server import GameServer, copy_world


class AmbientDialogueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = GameServer(('127.0.0.1', 0), Path(self.tmp.name)/'save.json')
        self.addCleanup(self.server.server_close)
        self.w = self.server.world
        self.w.data.update(awake=True, habitat_open=True)
        for key, b in self.w.data['birds'].items():
            b['room'] = 'garden' if key in ('pip', 'moss') else ('archive' if key == 'zip' else 'nursery')

    def test_pair_uses_shared_model_and_becomes_heard_archived_speech(self):
        with patch('server.exchange', return_value=['Would this fern enjoy a tiny hat?', 'Only if the hat has room for sunshine.']):
            self.assertTrue(self.server.ambient_once())
        events = self.w.data['voices'][-2:]
        self.assertEqual([(e['bird'], e['target']) for e in events], [('pip','moss'), ('moss','pip')])
        self.assertIn('fern', self.w.archive.retrieve('moss','fern')['words'])
        self.assertIn('sunshine', self.w.archive.retrieve('pip','sunshine')['words'])
        self.assertFalse(self.server.chat_lock.locked())

    def test_player_priority_or_movement_discards_stale_exchange(self):
        def interrupted(*args):
            self.server.last_user_chat = time.monotonic()
            return ['A new topic.', 'A different answer.']
        with patch('server.exchange', side_effect=interrupted):
            self.assertFalse(self.server.ambient_once())
        self.assertFalse(self.w.data.get('voices'))
        def moved(*args):
            self.w.data['birds']['moss']['room'] = 'archive'
            return ['A new topic.', 'A different answer.']
        with patch('server.exchange', side_effect=moved):
            self.assertFalse(self.server.ambient_once())

    def test_model_failure_and_disabled_state_leave_native_game_running(self):
        with patch('server.exchange', side_effect=OSError('not installed')):
            self.assertFalse(self.server.ambient_once())
        self.assertFalse(self.server.chat_lock.locked())
        self.w.data['natural_conversations'] = False
        with patch('server.exchange') as model:
            self.assertFalse(self.server.ambient_once())
            model.assert_not_called()

    def test_exchange_parses_and_rejects_repeated_lines(self):
        payload = {'message': {'content': json.dumps({'first':'Hello fern.', 'second':'Hello fern!'})}}
        with patch('ambient_dialogue.urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())):
            with self.assertRaises(ValueError):
                exchange(copy_world(self.w), 'pip', 'moss', 'Garden')
