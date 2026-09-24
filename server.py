"""Loopback-only local game server. Python standard library; optional local Ollama."""
import argparse
import json
import mimetypes
import os
import re
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from game import BIRDS, ROOT, World

from conversation import dialogue, MODEL
from ambient_dialogue import exchange


class GameServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, save_path):
        self.world = World(save_path)
        self.lock = threading.RLock()
        self.chat_lock = threading.Lock()
        self.last_visit = time.monotonic()
        self.stopped = threading.Event()
        self.last_user_chat = 0.
        self.ambient_serial = 0
        self.ambient_started = False
        super().__init__(address, Handler)

    def clock(self):
        if not self.ambient_started:
            self.ambient_started = True
            threading.Thread(target=self.ambient_clock, daemon=True).start()
        while not self.stopped.wait(5):
            if time.monotonic() - self.last_visit < 15:
                try:
                    with self.lock:
                        self.world.tick()
                except Exception as exc:
                    print(f'World clock paused after save error: {exc}', flush=True)
                    with self.lock:
                        self.world.data['paused'] = True

    def ambient_clock(self):
        while not self.stopped.wait(45):
            if time.monotonic() - self.last_visit >= 15 or time.monotonic() - self.last_user_chat < 30:
                continue
            self.ambient_once()

    def ambient_once(self):
        if not self.chat_lock.acquire(blocking=False):
            return False
        try:
            with self.lock:
                world = self.world
                if world.data['paused'] or not world.data['habitat_open'] or not world.data.get('natural_conversations', True):
                    return False
                rooms = {}
                for key, bird in world.data['birds'].items():
                    rooms.setdefault(world.room_of(bird), []).append(key)
                choices = [(room, members) for room, members in rooms.items() if len(members) >= 2]
                if not choices:
                    return False
                room, members = choices[self.ambient_serial % len(choices)]
                a, b = members[self.ambient_serial % len(members)], members[(self.ambient_serial+1) % len(members)]
                self.ambient_serial += 1
                user_before = self.last_user_chat
                snapshot = copy_world(world, text=world.spaces()[room]['name'])
            lines = exchange(snapshot, a, b, world.spaces()[room]['name'])
            with self.lock:
                if (self.stopped.is_set() or self.last_user_chat != user_before or world.data['paused']
                        or time.monotonic() - self.last_visit >= 15
                        or not world.data.get('natural_conversations', True)
                        or any(world.room_of(world.data['birds'][k]) != room for k in (a, b))):
                    return False
                from speech_memory import is_fresh
                if not all(is_fresh(world.data, line) for line in lines):
                    return False
                world.lonk_say(a, lines[0], b)
                world.lonk_say(b, lines[1], a)
                world.stimulate(a, 'MusicPulse')
                world.stimulate(b, 'MusicPulse')
                world.data['ambient_voice_status'] = 'Local Qwen conversation'
                world.save()
                return True
        except (OSError, ValueError, KeyError, TypeError):
            return False  # Native learned conversation continues without the model.
        finally:
            self.chat_lock.release()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if args and str(args[1] if len(args) > 1 else '') not in ('200', '304'):
            super().log_message(fmt, *args)

    def allowed(self):
        host = self.headers.get('Host', '')
        valid_hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        origin = self.headers.get('Origin')
        return host in valid_hosts and (not origin or origin in {f'http://{h}' for h in valid_hosts})

    def send(self, data, status=200, kind='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8') if isinstance(data, (dict, list)) else data
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if not self.allowed():
            return self.send({'error': 'Local game access only.'}, 403)
        path = urlparse(self.path).path
        if path == '/api/state':
            self.server.last_visit = time.monotonic()
            with self.server.lock:
                return self.send(self.server.world.payload())
        if path == '/api/health':
            return self.send({'game': 'little-flock', 'ok': True, 'version': 'evolving-worlds-9'})
        static = {'/builder.js': 'builder.js', '/builder.css': 'builder.css', '/life.js': 'life.js', '/life.css': 'life.css', '/space-art.js': 'space-art.js', '/worlds.js': 'worlds.js', '/worlds.css': 'worlds.css', '/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/society.css': 'society.css', '/favicon.svg': 'favicon.svg'}
        if path not in static:
            return self.send({'error': 'Not found.'}, 404)
        file = ROOT / 'web' / static[path]
        mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        return self.send(file.read_bytes(), kind=mime + ('; charset=utf-8' if mime.startswith('text/') else ''))

    def do_POST(self):
        if not self.allowed():
            return self.send({'error': 'Local game access only.'}, 403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192 or self.headers.get_content_type() != 'application/json':
                return self.send({'error': 'Send a small JSON request.'}, 400)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError('Expected a JSON object.')
            path = urlparse(self.path).path
            if path == '/api/action':
                action, bird = body.get('action'), body.get('bird', 'pip')
                if not isinstance(action, str) or not isinstance(bird, str):
                    raise ValueError('Invalid action or bird.')
                with self.server.lock:
                    reply = self.server.world.act(action, bird, body.get('value'))
                    return self.send({'reply': reply, 'state': self.server.world.payload()})
            if path == '/api/chat':
                text, bird = body.get('text', ''), body.get('bird', 'pip')
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= 600 or not isinstance(bird, str) or bird not in self.server.world.specs:
                    raise ValueError('Choose a bird and write 1-600 characters.')
                text = text.strip()
                self.server.last_user_chat = time.monotonic()
                if not self.server.chat_lock.acquire(timeout=28):
                    return self.send({'error': 'One bird is still speaking. Give them a moment.'}, 409)
                try:
                    with self.server.lock:
                        world = self.server.world
                        world.require(world.data['awake'], 'Wake Pip first.')
                        world.require(bird == 'pip' or world.data['habitat_open'], 'Meet the flock first.')
                        match = re.search(r'my favorite (movie|song) is (.{1,100})', text, re.I)
                        if match:
                            world.data['facts'][match[1].lower()] = match[2].strip().rstrip('.!')
                        world.emit(bird, text, 'user', bird)
                        world.learn_text(bird, text)
                        world.save()
                        # Snapshot: model inference never holds the world clock lock.
                        snapshot = copy_world(world, bird, text)
                    reply, renderer = dialogue(snapshot, bird, text)
                    with self.server.lock:
                        # Recheck against live chatter generated during model inference.
                        if reply and not world.emit(bird, reply, 'reply', 'user'):
                            reply, renderer = '', 'quiet'
                        world.data['chats'].append({'bird': bird, 'role': 'user', 'text': text})
                        if reply:
                            world.data['chats'].append({'bird': bird, 'role': 'assistant', 'text': reply, 'renderer': renderer})
                        world.data['chats'] = world.data['chats'][-48:]
                        world.stimulate(bird, 'Quiet')
                        world.save()
                        return self.send({'reply': reply, 'renderer': renderer, 'state': world.payload()})
                finally:
                    self.server.chat_lock.release()
            return self.send({'error': 'Not found.'}, 404)
        except (ValueError, TypeError, KeyError) as exc:
            return self.send({'error': str(exc)}, 400)
        except Exception as exc:
            print(f'Request failed: {exc}', flush=True)
            return self.send({'error': 'Could not save that action. Check the local server log.'}, 500)


def copy_world(world, bird=None, text=''):
    import copy
    from types import SimpleNamespace
    return SimpleNamespace(data=copy.deepcopy(world.data), specs=copy.deepcopy(world.specs),
                           brains=copy.deepcopy(world.brains), society_context=world.society.payload(),
                           life_context={key: world.lonk_profile(key) for key in world.specs},
                           archive_context={key: world.archive.retrieve(key, text) for key in ([bird] if bird else world.specs)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8877)
    parser.add_argument('--save', type=Path, default=Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'LittleFlock' / 'save.json')
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    try:
        server = GameServer(('127.0.0.1', args.port), args.save)
    except OSError as exc:
        raise SystemExit(f'Cannot start Little Flock on port {args.port}: {exc}')
    threading.Thread(target=server.clock, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Little Flock is home at {url}\nSave: {args.save}\nClose this server to stop. Your flock rests while you are away.', flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stopped.set()
        server.server_close()


if __name__ == '__main__':
    main()
