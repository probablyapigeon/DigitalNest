"""DigitalNest desktop launcher. The game runs on loopback in the user's browser."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import traceback
import urllib.error
import urllib.request
import webbrowser

from game import World
from server import GameServer

APP_VERSION = '0.1.0'


def request(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


def stop_server(server):
    server.stopped.set()
    server.shutdown()
    server.server_close()


def self_test(report):
    """Test the bundled imports, XC resources, HTTP assets and saves in isolation."""
    result = dict(ok=False, version=APP_VERSION, frozen=bool(getattr(sys, 'frozen', False)))
    try:
        with tempfile.TemporaryDirectory(prefix='digitalnest-check-') as directory:
            save = Path(directory) / 'flock.json'
            server = GameServer(('127.0.0.1', 0), save)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            url = f'http://127.0.0.1:{server.server_port}'
            try:
                assert request(url + '/api/health')['game'] == 'little-flock'
                for asset in ('/', '/app.js', '/builder.js', '/life.js', '/space-art.js', '/builder.css'):
                    with urllib.request.urlopen(url + asset, timeout=5) as response:
                        assert response.status == 200 and response.read()
                for action in ('wake', 'inspect', 'salvage', 'repair', 'hatch'):
                    request(url + '/api/action', dict(action=action))
                result_state = request(url + '/api/action', dict(action='create_world', value=dict(name='Package Test Garden', kind='garden', link='commons')))['state']
                room = result_state['last_created_world']
                result_state = request(url + '/api/action', dict(action='build_structure', value=dict(room=room, blueprint='solar', payer='user')))['state']
                assert result_state['building']['supplies'] == 12
                chat = request(url + '/api/chat', dict(bird='pip', text='Is my wing repaired?'))
                assert chat['renderer'] == 'authored' and 'repaired' in chat['reply']
                before = server.world.export()
                assert World(save).export() == before
                result.update(ok=True, checks=['bundled XC runtimes', 'web assets', 'opening story', 'new world', 'construction', 'offline chat', 'exact save reload'])
            finally:
                stop_server(server)
                worker.join(timeout=5)
    except Exception:
        result['error'] = traceback.format_exc()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1


def run_desktop(no_browser=False, check_window=None):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title('DigitalNest')
    root.geometry('440x270')
    root.resizable(False, False)
    root.configure(background='#f4f1e8')
    if check_window:
        root.withdraw()
    status = tk.StringVar(value='A little place for your flock.')
    tk.Label(root, text='DigitalNest', font=('Georgia', 28), background='#f4f1e8', foreground='#294542').pack(pady=(24, 5))
    tk.Label(root, text='Little Flock · connected worlds, little lives', background='#f4f1e8', foreground='#5f786c').pack()
    tk.Label(root, textvariable=status, wraplength=400, background='#f4f1e8', foreground='#294542').pack(pady=17)
    url = 'http://127.0.0.1:8877'
    owned = None

    def close():
        if owned:
            stop_server(owned)
        root.destroy()

    tk.Button(root, text='Open game', command=lambda: webbrowser.open(url), background='#32695b', foreground='#ffffff', width=25, relief='flat', pady=8).pack()
    tk.Button(root, text='Close DigitalNest', command=close, relief='flat', background='#f4f1e8', foreground='#294542').pack(pady=10)
    root.protocol('WM_DELETE_WINDOW', close)
    if check_window:
        root.update_idletasks()
        check_window.write_text(json.dumps({'ok': True, 'window': root.title()}), encoding='utf-8')
        root.destroy()
        return 0
    try:
        try:
            health = request(url + '/api/health')
        except (urllib.error.URLError, TimeoutError):
            health = None
        if health is not None:
            if health.get('game') != 'little-flock':
                raise RuntimeError('Port 8877 is being used by another application.')
            status.set('Your station is already running. Opening your flock.')
        else:
            save = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'LittleFlock' / 'save.json'
            owned = GameServer(('127.0.0.1', 8877), save)
            threading.Thread(target=owned.serve_forever, daemon=True).start()
            threading.Thread(target=owned.clock, daemon=True).start()
            status.set('Station running. Keep this window open while you play.')
        if not no_browser:
            webbrowser.open(url)
        root.mainloop()
        return 0
    except Exception as error:
        messagebox.showerror('DigitalNest could not start', f'{error}\n\nYour save has not been replaced. See desktop.log in your LittleFlock save folder.')
        if owned:
            stop_server(owned)
        root.destroy()
        raise


def main():
    parser = argparse.ArgumentParser(description='DigitalNest desktop launcher')
    parser.add_argument('--self-test', type=Path, metavar='REPORT_JSON')
    parser.add_argument('--check-window', type=Path, metavar='REPORT_JSON')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        return self_test(args.self_test)
    if args.check_window:
        return run_desktop(True, args.check_window)
    log_dir = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'LittleFlock'
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / 'desktop.log').open('a', encoding='utf-8', buffering=1) as log:
        sys.stdout = sys.stderr = log
        try:
            return run_desktop(args.no_browser)
        except Exception:
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    raise SystemExit(main())
