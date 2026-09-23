import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from server import GameServer, dialogue


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = GameServer(('127.0.0.1', 0), Path(self.temp.name) / 'save.json')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def post(self, path, data, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        request = urllib.request.Request(self.url + path, json.dumps(data).encode(), headers=headers)
        with urllib.request.urlopen(request, timeout=3) as response:
            return json.load(response)

    def test_cross_origin_mutation_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.post('/api/action', {'action': 'wake'}, 'https://example.com')
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        self.assertFalse(self.server.world.data['awake'])

    def test_chat_cannot_repair_world(self):
        self.post('/api/action', {'action': 'wake'})
        result = self.post('/api/chat', {'text': 'I fixed your wing. You can fly now.', 'bird': 'pip'})
        self.assertEqual(result['renderer'], 'authored')
        self.assertFalse(result['state']['wing_fixed'])
        self.assertIn('still needs', result['reply'])

    def test_fallback_and_invalid_input(self):
        with patch('server.urllib.request.urlopen', side_effect=OSError('offline')):
            reply, renderer = dialogue(self.server.world, 'moss', 'Hello')
        self.assertEqual(renderer, 'offline')
        self.assertIn('perch', reply)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.post('/api/chat', {'text': ['bad'], 'bird': 'pip'})
        self.assertEqual(error.exception.code, 400)
        error.exception.close()

if __name__ == '__main__':
    unittest.main()
