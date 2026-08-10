#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
ADMIN_DIR="$ROOT_DIR/admin-frontend"
H5_DIR="$ROOT_DIR/h5-frontend"
PYTHON_BIN="${PYTHON_BIN:-/Users/simon/.workbuddy/binaries/python/versions/3.13.12/bin/python3}"
VENV_DIR="$BACKEND_DIR/.venv"

PIDS=()

print_banner() {
  printf '\n微站开发服务已启动：\n'
  printf '  后端 API： http://localhost:8000/docs\n'
  printf '  后台管理： http://localhost:5173/admin/\n'
  printf '  移动端 H5： http://localhost:5174/\n'
  printf '\n按 Ctrl+C 可同时停止全部服务。\n\n'
}

cleanup() {
  trap - EXIT INT TERM
  printf '\n正在停止开发服务...\n'
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  printf '所有开发服务已停止。\n'
}

require_dir() {
  if [[ ! -d "$1" ]]; then
    printf '缺少目录：%s\n' "$1" >&2
    exit 1
  fi
}

start_service() {
  local name="$1"
  local dir="$2"
  shift 2

  printf '[启动] %s\n' "$name"
  (
    cd "$dir"
    exec "$@"
  ) &
  PIDS+=("$!")
}

require_dir "$BACKEND_DIR"
require_dir "$ADMIN_DIR"
require_dir "$H5_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  printf '未找到 Python：%s\n请通过 PYTHON_BIN 指定可用的 Python 解释器。\n' "$PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  printf '[准备] 创建后端虚拟环境...\n'
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c "import uvicorn" >/dev/null 2>&1; then
  printf '[准备] 安装后端依赖...\n'
  "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

if [[ ! -d "$ADMIN_DIR/node_modules" ]]; then
  printf '[准备] 安装后台管理依赖...\n'
  (cd "$ADMIN_DIR" && /Users/simon/.workbuddy/binaries/node/versions/22.22.2/bin/npm install)
fi

if [[ ! -d "$H5_DIR/node_modules" ]]; then
  printf '[准备] 安装移动端依赖...\n'
  (cd "$H5_DIR" && /Users/simon/.workbuddy/binaries/node/versions/22.22.2/bin/npm install)
fi

trap cleanup EXIT INT TERM

start_service "后端 API" "$BACKEND_DIR" "$VENV_DIR/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
start_service "后台管理" "$ADMIN_DIR" /Users/simon/.workbuddy/binaries/node/versions/22.22.2/bin/npm run dev -- --host 0.0.0.0 --port 5173
start_service "移动端 H5" "$H5_DIR" /Users/simon/.workbuddy/binaries/node/versions/22.22.2/bin/npm run dev -- --host 0.0.0.0 --port 5174

print_banner
wait
