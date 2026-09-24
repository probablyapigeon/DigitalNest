import tempfile
import unittest
from pathlib import Path

from game import World
from server import copy_world, dialogue
from unittest.mock import patch


class LonkLifeTests(unittest.TestCase):
    def test_gossip_does_not_requote_generated_memories_or_repeat_recent_lines(self):
        w = self.world
        w.society.bird('pip').remember('I remember: I remember: forbidden echo')
        lines = []
        for _ in range(20):
            line = w.act('lonk_life', 'pip', {'event': 'gossip', 'target': 'moss'})
            self.assertNotIn('forbidden echo', line)
            self.assertNotIn('I remember:', line)
            self.assertNotIn(line, lines[-6:])
            lines.append(line)
            w.data['tick'] += 2
        w.save()
        restored = World(w.path)
        self.assertEqual(restored.export(), w.export())
        next_line = restored.act('lonk_life', 'pip', {'event': 'gossip', 'target': 'moss'})
        self.assertNotIn(next_line, lines[-6:])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.world = World(Path(self.tmp.name) / 'save.json')
        self.world.data.update(awake=True, habitat_open=True)
        for bird in self.world.data['birds'].values():
            bird['room'] = 'garden'

    def test_individual_keepsakes_and_emotions_survive_reload(self):
        w = self.world
        moss_before = len(w.society.bird('moss').inventory)
        pip_before = list(w.society.bird('pip').inventory)
        w.act('lonk_life', 'moss', {'event': 'forage'})
        self.assertEqual(len(w.society.bird('moss').inventory), moss_before + 1)
        self.assertEqual(w.society.bird('pip').inventory, pip_before)
        self.assertTrue(w.society.bird('moss').catchphrase)
        self.assertEqual(World(w.path).export(), w.export())
        before = w.export()
        with self.assertRaises(ValueError):
            w.act('lonk_life', 'moss', {'event': 'forage'})
        self.assertEqual(before, w.export())

    def test_contest_is_local_persistent_and_noninjurious(self):
        w = self.world
        w.data['birds']['zip']['room'] = 'workshop'
        before = w.export()
        with self.assertRaises(ValueError):
            w.act('lonk_life', 'pip', {'event': 'contest', 'target': 'zip'})
        self.assertEqual(before, w.export())
        w.data['birds']['zip']['room'] = 'garden'
        w.act('lonk_life', 'pip', {'event': 'contest', 'target': 'zip'})
        self.assertEqual(w.lonk_profile('pip')['rival'], 'zip')
        self.assertEqual(w.lonk_profile('zip')['rival'], 'pip')
        self.assertEqual(w.society.bird('zip').trauma, 0)
        self.assertEqual(World(w.path).lonk_profile('pip'), w.lonk_profile('pip'))

    def test_gossip_teaches_present_friend_and_dreams_are_silent(self):
        w = self.world
        w.learn_text('pip', 'moonwaffle')
        w.data['birds']['alto']['room'] = 'roost'
        before = w.society.bird('alto').linguistics['total_heard']
        w.act('lonk_life', 'pip', {'event': 'gossip', 'target': 'moss'})
        self.assertIn('moonwaffle', w.society.bird('moss').linguistics['tokens'])
        self.assertEqual(before, w.society.bird('alto').linguistics['total_heard'])
        w.act('lonk_life', 'zip', {'event': 'dream'})
        self.assertEqual(w.data['voices'][-1]['kind'], 'thought')
        self.assertIn('dream', w.lonk_profile('zip'))

    def test_native_emotional_clock_runs_and_pause_freezes_it(self):
        w = self.world
        before = w.society.bird('pip').xc_checkpoint
        w.tick()
        self.assertNotEqual(before, w.society.bird('pip').xc_checkpoint)
        self.assertEqual(sum(w.society.bird('pip').habits.values()), 1)
        w.data['paused'] = True
        before = w.export()
        w.tick()
        self.assertEqual(before, w.export())

    def test_offline_chat_knows_actual_keepsake(self):
        w = self.world
        w.act('lonk_life', 'pip', {'event': 'forage'})
        with patch('server.urllib.request.urlopen', side_effect=OSError('offline')):
            reply, renderer = dialogue(copy_world(w), 'pip', 'What did you find?')
        self.assertIn(w.lonk_profile('pip')['treasure'], reply)
        self.assertEqual(renderer, 'offline')

    def test_keepsake_gift_moves_one_real_item_and_records_origin(self):
        w = self.world
        w.act('lonk_life', 'pip', {'event': 'forage'})
        item = w.lonk_profile('pip')['treasure']
        count = sum(len(w.society.bird(k).inventory) for k in w.specs)
        w.data['tick'] += 2
        w.act('lonk_life', 'pip', {'event': 'keepsake_gift', 'target': 'moss'})
        self.assertEqual(sum(len(w.society.bird(k).inventory) for k in w.specs), count)
        self.assertEqual(w.lonk_profile('moss')['treasure'], item)
        self.assertTrue(any('Pip gave me' in m['text'] for m in w.lonk_profile('moss')['memories']))
        self.assertEqual(World(w.path).export(), w.export())
