"""Local developer launcher. Never kills another process to reclaim a port."""
import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--live', action='store_true', help='Enable explicit opt-in live domain checks')
args = parser.parse_args()
for port in (8000, 5173):
    with socket.socket() as check:
        try:
            check.bind(('127.0.0.1', port))
        except OSError:
            sys.exit(f'Port {port} is occupied. Stop its existing terminal with Ctrl+C, or open http://127.0.0.1:5173 if PhishX is already running. Inspect with: lsof -nP -iTCP:{port} -sTCP:LISTEN')
model = root / 'artifacts/revised-run06/classical.joblib'
if not model.is_file():
    sys.exit('Missing trusted model handoff: artifacts/revised-run06/classical.joblib')
pnpm = shutil.which('pnpm')
if not pnpm:
    fallback = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm'
    pnpm = str(fallback) if fallback.is_file() else None
if not pnpm:
    sys.exit('pnpm is not available. Install pnpm or add its launcher to PATH.')
env = dict(os.environ, PYTHONPATH=os.pathsep.join(['ml', '.']), PHISHX_MODE='model',
           PHISHX_PROVIDER='ml.integration:create_provider', PHISHX_MODEL_PATH=str(model),
           PHISHX_LIVE_SIGNALS='1' if args.live else '0')
children = []
def stop(*_):
    for child in children:
        if child.poll() is None:
            child.terminate()
signal.signal(signal.SIGTERM, stop)
try:
    children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log'], cwd=root, env=env))
    children.append(subprocess.Popen([pnpm, 'dev'], cwd=root/'frontend', env=env))
    print('PhishX: http://127.0.0.1:5173 — Ctrl+C stops both services.', flush=True)
    while all(child.poll() is None for child in children):
        time.sleep(.5)
except KeyboardInterrupt:
    pass
finally:
    stop()
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
