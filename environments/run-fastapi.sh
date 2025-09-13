#!/bin/sh
set -eu

WS="${WORKSPACE:-/home/jenkins/agent/workspace}"
MODULE="${1:-${APP_MODULE:-app.main:app}}"
PORT="${PORT:-9000}"

echo "[run-fastapi] Workspace: $WS"
cd "$WS"

# Install per-repo dependencies if present
if [ -f requirements.txt ]; then
  echo "[run-fastapi] Installing requirements.txt..."
  pip3 install --no-cache-dir -r requirements.txt
else
  echo "[run-fastapi] No requirements.txt found; skipping."
fi

echo "[run-fastapi] Launching Uvicorn: ${MODULE} on 0.0.0.0:${PORT}"
exec uvicorn "$MODULE" --host 0.0.0.0 --port "$PORT"
