#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

# ensure requirements installed (best-effort)
if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt || true
fi

# choose a preferred port from this list (uses the first free)
PREFERRED_PORTS=(8001 3000 8000)
PORT=""
for p in "${PREFERRED_PORTS[@]}"; do
  if ! lsof -iTCP:${p} -sTCP:LISTEN >/dev/null 2>&1; then
    PORT=${p}
    break
  fi
done
if [ -z "$PORT" ]; then
  # pick any free ephemeral port using Python
  PORT=$(python3 - <<'PY'
import socket
s=socket.socket()
s.bind(('127.0.0.1',0))
port = s.getsockname()[1]
s.close()
print(port)
PY
)
  echo "No preferred port free; using ephemeral free port: $PORT"
fi

echo "Starting watcher+server on port $PORT"
python3 scripts/watch_and_serve.py --port "$PORT"
