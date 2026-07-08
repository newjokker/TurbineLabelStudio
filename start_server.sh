#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

export PYTHONPATH="$BASE_DIR${PYTHONPATH:+:$PYTHONPATH}"

api_pid=""
download_pid=""

stop_all() {
  echo "Stopping services..."

  [[ -n "${api_pid:-}" ]] && kill "$api_pid" 2>/dev/null || true
  [[ -n "${download_pid:-}" ]] && kill "$download_pid" 2>/dev/null || true

  wait || true
}

trap stop_all SIGTERM SIGINT EXIT

echo "Starting API server..."
"$PYTHON_BIN" -u app/api_server.py &
api_pid="$!"

echo "Starting Download daemon..."
"$PYTHON_BIN" -u download.py &
download_pid="$!"

sleep 1

kill -0 "$api_pid" 2>/dev/null || {
  echo "API server failed to start"
  exit 1
}

kill -0 "$download_pid" 2>/dev/null || {
  echo "Download daemon failed to start"
  exit 1
}

echo "All services started."
echo "API PID: $api_pid"
echo "Download PID: $download_pid"

wait -n "$api_pid" "$download_pid"

echo "One service exited, shutting down container."
exit 1