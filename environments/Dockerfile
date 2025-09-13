FROM python:3.12-slim

# Prevent Python from writing .pyc and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # venv path we will reuse across restarts
    VENV_PATH=/docker_venv \
    # app mount path (code bind-mounted by Jenkins)
    APP_DIR=/app

# curl used by healthcheck and small scripts, procps for kill signals
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl procps ca-certificates git \
 && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 10001 appuser

# venv: mounted /app so it persists across code changes
RUN python -m venv "$VENV_PATH" \
 && "$VENV_PATH/bin/pip" install --upgrade pip wheel uvicorn==0.30.* watchdog==4.* \
 && mkdir -p "$APP_DIR" /cache \
 && chown -R appuser:appuser "$APP_DIR" "$VENV_PATH" /cache

WORKDIR $APP_DIR
USER appuser

# Simple bootstrap that:
# 1) Installs deps if requirements.txt hash has changed
# 2) Starts uvicorn with --reload so code changes in the mount are picked up
#    (fine for dev/test; do not use --reload for prod)
COPY --chown=appuser:appuser <<'EOF' /usr/local/bin/boot.sh
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
VENV_PATH="${VENV_PATH:-/venv}"
REQ="$APP_DIR/requirements.txt"
STAMP="/cache/requirements.sha256"

# If requirements exist and changed, install
if [ -f "$REQ" ]; then
  CURR_SHA="$(sha256sum "$REQ" | awk '{print $1}')"
  PREV_SHA=""
  [ -f "$STAMP" ] && PREV_SHA="$(cat "$STAMP")"
  if [ "$CURR_SHA" != "$PREV_SHA" ]; then
    echo "Installing Python dependencies..."
    "$VENV_PATH/bin/pip" install --no-cache-dir -r "$REQ"
    echo "$CURR_SHA" > "$STAMP"
  else
    echo "Dependencies unchanged. Skipping install."
  fi
else
  echo "No requirements.txt found. Skipping install."
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-9000}"
APP_IMPORT="${APP_IMPORT:-main:app}"  # override if your app module differs

# Start FastAPI with reload for rapid dev feedback
exec "$VENV_PATH/bin/uvicorn" "$APP_IMPORT" --host "$HOST" --port "$PORT" --reload
EOF

RUN chmod +x /usr/local/bin/boot.sh

EXPOSE 9000

# Healthcheck tries /health then /; keep it lenient
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=5 \
  CMD curl -fsS http://127.0.0.1:9000/health || curl -fsS http://127.0.0.1:9000/ || exit 1

ENTRYPOINT ["/usr/local/bin/boot.sh"]
