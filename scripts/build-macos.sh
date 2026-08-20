#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "此脚本必须在 macOS 上运行。" >&2
  exit 1
fi

if [[ ! -x .venv-build/bin/python ]]; then
  python3.11 -m venv .venv-build
fi
.venv-build/bin/python -m pip install --upgrade pip wheel
.venv-build/bin/python -m pip install -e . pyinstaller pytest
.venv-build/bin/python -m pytest
.venv-build/bin/python -m PyInstaller --noconfirm --clean build/desktop.spec

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
