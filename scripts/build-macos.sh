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
"$BUILD_VENV/bin/python" scripts/generate-icons.py macos
"$BUILD_VENV/bin/python" -m PyInstaller --noconfirm --clean build/desktop.spec

mkdir -p dist-installer
rm -f dist-installer/PaddleOCR-Desktop-0.1.0.dmg
if ! command -v create-dmg >/dev/null 2>&1; then
  echo "未找到 DMG 构建工具 create-dmg。" >&2
  echo "请执行：brew install create-dmg" >&2
  exit 1
fi
DMG_COMMAND="$(command -v create-dmg)"
if ! DMG_TOOL_VERSION="$(create-dmg --pure-version 2>/dev/null)"; then
  DETECTED_VERSION="$(create-dmg --version 2>/dev/null | head -n 1 || true)"
  echo "检测到不兼容的同名 create-dmg：$DMG_COMMAND" >&2
  if [[ -n "$DETECTED_VERSION" ]]; then
    echo "当前版本：$DETECTED_VERSION" >&2
  fi
  echo "本项目需要 Homebrew 提供的 create-dmg/create-dmg 1.x；npm 版不支持 Finder 图标布局参数。" >&2
  echo "请依次执行：" >&2
  echo "  npm uninstall -g create-dmg" >&2
  echo "  brew install create-dmg" >&2
  echo "  hash -r" >&2
  echo "然后重新运行本构建脚本。" >&2
  exit 1
fi
if [[ "$DMG_TOOL_VERSION" != 1.* ]]; then
  echo "create-dmg 版本不兼容：$DMG_TOOL_VERSION" >&2
  echo "当前命令：$DMG_COMMAND" >&2
  echo "本项目需要 Homebrew 提供的 create-dmg/create-dmg 1.x。" >&2
  echo "请执行：brew reinstall create-dmg && hash -r" >&2
  exit 1
fi
echo "使用 create-dmg $DMG_TOOL_VERSION"

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
ditto "dist/PaddleOCR Desktop.app" "$DMG_STAGE/PaddleOCR Desktop.app"

create-dmg \
  --volname "PaddleOCR Desktop" \
  --window-pos 200 120 \
  --window-size 720 460 \
  --text-size 14 \
  --icon-size 128 \
  --app-drop-link 520 225 \
  --icon "PaddleOCR Desktop.app" 200 225 \
  --hide-extension "PaddleOCR Desktop.app" \
  --no-internet-enable \
  --format UDZO \
  "dist-installer/PaddleOCR-Desktop-0.1.0.dmg" \
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
  "dist-installer/PaddleOCR-Desktop-0.1.0.dmg" >/dev/null

if [[ ! -d "$VERIFY_MOUNT/PaddleOCR Desktop.app" ]]; then
  echo "DMG 校验失败：挂载卷中未找到应用。" >&2
  exit 1
fi
if [[ ! -L "$VERIFY_MOUNT/Applications" ]]; then
  echo "DMG 校验失败：挂载卷中未找到 Applications 拖拽入口。" >&2
  exit 1
fi
if [[ ! -f "$VERIFY_MOUNT/.DS_Store" ]]; then
  echo "DMG 校验失败：未找到 Finder 布局数据，挂载后可能无法显示安装界面。" >&2
  exit 1
fi
hdiutil detach "$VERIFY_MOUNT" -quiet
rmdir "$VERIFY_MOUNT"
trap - EXIT

echo "DMG 已验证，可挂载并拖动到 Applications 安装："
echo "dist-installer/PaddleOCR-Desktop-0.1.0.dmg"
