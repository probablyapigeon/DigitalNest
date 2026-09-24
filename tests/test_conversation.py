import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game import World
from server import copy_world
from conversation import dialogue, chat_messages
from speech_memory import is_fresh, remember_speech


def response(text):
    return io.BytesIO(json.dumps({'message': {'content': text}}).encode())


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.w = World(Path(self.tmp.name) / 'save.json')
        self.w.data.update(awake=True, habitat_open=True)

    def test_repeated_model_reply_retried_with_clean_current_question(self):
        self.w.data['chats'] = [dict(bird='pip', role='assistant', text='Shiny time!') for _ in range(3)]
        snapshot = copy_world(self.w)
        with patch('conversation.urllib.request.urlopen', side_effect=[response('SHINY TIME.'), response('A window expedition? I shall supervise the glass.')]) as call:
            reply, renderer = dialogue(snapshot, 'pip', 'TO THE WINDOW')
        self.assertEqual(renderer, 'local-model')
        self.assertIn('window', reply)
        retry = json.loads(call.call_args_list[1].args[0].data)['messages']
        self.assertEqual(retry[-1], {'role': 'user', 'content': 'TO THE WINDOW'})
        self.assertFalse(any(m['role'] == 'assistant' for m in retry))
        self.assertEqual(len(self.w.data['chats']), 3)

    def test_ledger_survives_reload_and_visible_history_expiry(self):
        self.assertTrue(self.w.emit('pip', 'Shiny time!', 'reply'))
        self.w.data['chats'] = []
        self.w.data['voices'] = []
        self.w.save()
        loaded = World(self.w.path)
        self.assertFalse(loaded.emit('moss', 'SHINY TIME.', 'speech'))
        self.assertFalse(loaded.emit('moss', 'Shiny time! Another thought.', 'speech'))
        self.assertTrue(loaded.emit('moss', 'The window looks interesting.', 'speech'))
        self.assertNotIn('spoken_phrases', loaded.payload())

    def test_import_existing_chat_and_allow_user_repetition(self):
        self.w.data['chats'] = [dict(bird='pip', role='assistant', text='Bonk approved.')]
        self.assertFalse(self.w.emit('pip', 'bonk approved!', 'reply'))
        self.assertTrue(self.w.emit('pip', 'Bonk approved.', 'user'))
        self.assertTrue(self.w.emit('pip', 'Something entirely different.', 'reply'))
        self.w.data['chats'] = []
        self.assertFalse(is_fresh(self.w.data, 'Bonk approved.'))

    def test_no_within_reply_echo_and_no_silent_catchphrase_fallback(self):
        self.assertFalse(is_fresh({}, 'Shiny time. Shiny time!'))
        snapshot = copy_world(self.w)
        snapshot.life_context['pip']['catchphrase'] = 'Shiny time'
        with patch('conversation.urllib.request.urlopen', side_effect=[response('Shiny time!'), response('Shiny time.')]):
            reply, renderer = dialogue(snapshot, 'pip', 'POOP')
        self.assertEqual(renderer, 'offline')
        self.assertNotEqual(reply.casefold().rstrip('.!'), 'shiny time')

    def test_exhausted_fallback_listens_instead_of_repeating(self):
        with patch('conversation.urllib.request.urlopen', side_effect=OSError('offline')):
            for _ in range(2):
                reply, _ = dialogue(copy_world(self.w), 'moss', 'Hello')
                self.assertTrue(self.w.emit('moss', reply, 'reply'))
            self.assertEqual(dialogue(copy_world(self.w), 'moss', 'Hello'), ('', 'quiet'))

    def test_context_excludes_catchphrase_and_recursive_memory_dump(self):
        self.w.data['birds']['pip']['inner_life'] = {'dream': 'I remember: ' * 200}
        self.w.society.bird('pip').catchphrase = 'Shiny time'
        self.w.data['chats'] = [dict(bird='pip', role='assistant', text='Shiny time!') for _ in range(3)]
        messages = chat_messages(copy_world(self.w), 'pip', 'A new topic please')
        self.assertLess(len(messages[0]['content']), 3000)
        self.assertNotIn('Shiny time', json.dumps(messages))
        self.assertNotIn('I remember: I remember:', json.dumps(messages))

    def test_other_bird_affection_not_hijacked_by_pip_quest(self):
        with patch('conversation.urllib.request.urlopen', return_value=response('You polished my feathers? I feel extravagantly cared for.')):
            reply, renderer = dialogue(copy_world(self.w), 'moss', '*fixes your wings my lil bb*')
        self.assertEqual(renderer, 'local-model')
        self.assertNotIn('Pip', reply)

    def test_repeated_quest_questions_stay_truthful_and_do_not_loop(self):
        with patch('conversation.urllib.request.urlopen') as model:
            for _ in range(2):
                reply, mode = dialogue(copy_world(self.w), 'pip', 'I fixed your wing')
                self.assertEqual(mode, 'authored')
                self.assertTrue(self.w.emit('pip', reply, 'reply'))
            self.assertEqual(dialogue(copy_world(self.w), 'pip', 'I fixed your wing'), ('', 'quiet'))
            model.assert_not_called()
        self.assertFalse(self.w.data['wing_fixed'])

    def test_automatic_conversations_are_reciprocal_and_room_local(self):
        society = self.w.society
        society.world.config['culture']['conversation_chance'] = 1
        rooms = {'pip': 'garden', 'moss': 'garden', 'zip': 'archive', 'alto': 'nursery'}
        society.tick(1, rooms)
        lines = society.drain()
        directed = [line for line in lines if ' -> ' in line]
        self.assertEqual(len(directed), 2)
        self.assertTrue(all('Pip' in line and 'Moss' in line for line in directed))
        self.assertEqual(society.world.config['culture']['conversation_chance'], 1)
        society.tick(2, dict(zip(rooms, ['a', 'b', 'c', 'd'])))
        self.assertFalse(any(' -> ' in line for line in society.drain()))
