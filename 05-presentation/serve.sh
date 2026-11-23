#!/usr/bin/env bash
# Serve the slides locally and open them in the browser.
# Usage:  ./serve.sh                 -> opens deck/index.html
#         ./serve.sh deck/index.html -> opens another page of 05-presentation/
# Stop with Ctrl+C.
set -euo pipefail
cd "$(dirname "$0")"
PAGE="${1:-deck/index.html}"
PORT="${PORT:-8000}"
# Pick the next free port if 8000 is taken
while python3 -c "import socket,sys; s=socket.socket(); sys.exit(s.connect_ex(('127.0.0.1',$PORT))!=0)"; do PORT=$((PORT+1)); done
URL="http://localhost:$PORT/$PAGE"
echo "Slides: $URL   (Ctrl+C to stop)"
( sleep 1; xdg-open "$URL" >/dev/null 2>&1 || true ) &
exec python3 -m http.server "$PORT" --bind 127.0.0.1
