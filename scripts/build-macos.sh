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

DMG_STAGE="$(mktemp -d /tmp/paddleocr-dmg-stage.XXXXXX)"
cleanup_stage() {
  case "$DMG_STAGE" in
    /tmp/paddleocr-dmg-stage.*)
      if [[ -d "$DMG_STAGE" && ! -L "$DMG_STAGE" ]]; then
        rm -rf -- "$DMG_STAGE"
      fi
      ;;
    *)
      echo "拒绝清理非预期的 DMG 临时目录：$DMG_STAGE" >&2
      ;;
  esac
}
trap cleanup_stage EXIT
ditto "dist/PaddleOCR病历识别.app" "$DMG_STAGE/PaddleOCR病历识别.app"

create-dmg \
  --volname "PaddleOCR 病历识别" \
  --window-pos 200 120 \
  --window-size 660 420 \
  --text-size 13 \
  --icon-size 112 \
  --app-drop-link 470 205 \
  --icon "PaddleOCR病历识别.app" 190 205 \
  --hide-extension "PaddleOCR病历识别.app" \
  --no-internet-enable \
  --format UDZO \
  "dist-installer/PaddleOCR-Medical-0.1.0.dmg" \
  "$DMG_STAGE"
cleanup_stage
trap - EXIT

# Verify the finished image as a real drag-to-install volume. A successful
# create-dmg process alone does not guarantee that Finder aliases were added.
VERIFY_MOUNT="$(mktemp -d /tmp/paddleocr-dmg-verify.XXXXXX)"
cleanup_mount() {
  if mount | grep -Fq "on $VERIFY_MOUNT "; then
    hdiutil detach "$VERIFY_MOUNT" -quiet || true
  fi
  rmdir "$VERIFY_MOUNT" 2>/dev/null || true
}
trap cleanup_mount EXIT
hdiutil attach \
  -nobrowse \
  -readonly \
  -mountpoint "$VERIFY_MOUNT" \
  "dist-installer/PaddleOCR-Medical-0.1.0.dmg" >/dev/null

if [[ ! -d "$VERIFY_MOUNT/PaddleOCR病历识别.app" ]]; then
  echo "DMG 校验失败：挂载卷中未找到应用。" >&2
  exit 1
fi
if [[ ! -L "$VERIFY_MOUNT/Applications" ]]; then
  echo "DMG 校验失败：挂载卷中未找到 Applications 拖拽入口。" >&2
  exit 1
fi
hdiutil detach "$VERIFY_MOUNT" -quiet
rmdir "$VERIFY_MOUNT"
trap - EXIT

echo "DMG 已验证，可挂载并拖动到 Applications 安装："
echo "dist-installer/PaddleOCR-Medical-0.1.0.dmg"
