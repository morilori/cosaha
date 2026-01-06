#!/usr/bin/env python3
"""Watch the Art/ folder, regenerate folderImages.json on changes, and serve the site.

Usage:
  python3 scripts/watch_and_serve.py [--port 8000] [--interval 1.5]

This script uses a simple polling approach (no external deps) to detect file changes.
"""
import os
import time
import json
import urllib.parse
import argparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art'
OUT = ROOT / 'folderImages.json'


def is_image(n):
    n = n.lower()
    return n.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))


def collect():
    d = {}
    for dirpath, dirs, files in os.walk(ART):
        imgs = [f for f in files if is_image(f)]
        if not imgs:
            continue
        imgs_sorted = sorted(imgs, key=lambda s: s.lower())
        rel_dir = os.path.relpath(dirpath, ROOT).replace('\\', '/')
        if not rel_dir.endswith('/'):
            rel_dir = rel_dir + '/'
        paths = [f"{rel_dir}{f}".replace('\\', '/') for f in imgs_sorted]
        quoted = [urllib.parse.quote(p) for p in paths]
        d[rel_dir] = quoted
    return d


def write_json(d):
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf8')


def files_snapshot():
    m = {}
    for dirpath, dirs, files in os.walk(ART):
        for f in files:
            if not is_image(f):
                continue
            p = Path(dirpath) / f
            try:
                m[str(p)] = p.stat().st_mtime
            except FileNotFoundError:
                m[str(p)] = 0
    return m


def serve(port, interval):
    # initial generate
    if not ART.exists():
        print('No Art/ directory found at', ART)
        return
    prev = files_snapshot()
    data = collect()
    write_json(data)
    print(f'Wrote {OUT} with {len(data)} folders')

    # start file watcher using watchdog if available (more efficient); otherwise fall back to polling
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class RegenHandler(FileSystemEventHandler):
            def __init__(self):
                self._timer = None

            def _debounced_regen(self):
                try:
                    data = collect()
                    write_json(data)
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), f'Updated {OUT} ({len(data)} folders)')
                except Exception as e:
                    print('Error regenerating folderImages.json:', e)

            def on_any_event(self, event):
                # debounce rapid events
                if self._timer:
                    self._timer.cancel()
                import threading
                self._timer = threading.Timer(0.6, self._debounced_regen)
                self._timer.daemon = True
                self._timer.start()

        observer = Observer()
        handler = RegenHandler()
        observer.schedule(handler, str(ART), recursive=True)
        observer.daemon = True
        observer.start()
        print('Watching', ART, 'with watchdog')
    except Exception:
        # fallback to polling
        import threading

        def watcher():
            nonlocal prev
            while True:
                time.sleep(interval)
                snap = files_snapshot()
                if snap != prev:
                    try:
                        data = collect()
                        write_json(data)
                        print(time.strftime('%Y-%m-%d %H:%M:%S'), f'Updated {OUT} ({len(data)} folders)')
                    except Exception as e:
                        print('Error regenerating folderImages.json:', e)
                    prev = snap

        t = threading.Thread(target=watcher, daemon=True)
        t.start()

    os.chdir(ROOT)
    addr = ('0.0.0.0', port)
    httpd = ThreadingHTTPServer(addr, SimpleHTTPRequestHandler)
    print(f'Serving HTTP on {addr[0]} port {addr[1]} (http://localhost:{addr[1]}) ...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Stopping server')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8001)
    p.add_argument('--interval', type=float, default=1.5)
    args = p.parse_args()
    serve(args.port, args.interval)
