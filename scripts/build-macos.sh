#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "此脚本必须在 macOS 上运行。" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3.12}"
BUILD_VENV=".venv-build-py312"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "未找到 Python 3.12。请先运行：brew install python@3.12" >&2
  exit 1
fi

if [[ ! -x "$BUILD_VENV/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$BUILD_VENV"
fi
"$BUILD_VENV/bin/python" -m pip install --upgrade pip setuptools wheel
"$BUILD_VENV/bin/python" -m pip install -e . pyinstaller pytest
"$BUILD_VENV/bin/python" -m pytest
"$BUILD_VENV/bin/python" -m PyInstaller --noconfirm --clean build/desktop.spec

mkdir -p dist-installer
rm -f dist-installer/PaddleOCR-Medical-0.1.0.dmg
if ! command -v create-dmg >/dev/null 2>&1; then
  echo "未找到 create-dmg。请先运行：brew install create-dmg" >&2
  exit 1
fi
create-dmg \
  --volname "PaddleOCR 病历识别" \
  --window-size 660 420 \
  --icon-size 112 \
  --app-drop-link 470 205 \
  --icon "PaddleOCR病历识别.app" 190 205 \
  "dist-installer/PaddleOCR-Medical-0.1.0.dmg" \
  "dist/PaddleOCR病历识别.app"
echo "DMG 位于 dist-installer 目录。"
