from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "assets" / "app-icon.svg"
OUTPUT_DIR = ROOT / "assets" / "generated"


def render_png(size: int, output: Path) -> None:
    renderer = QSvgRenderer(QByteArray(SVG_PATH.read_bytes()))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid SVG icon: {SVG_PATH}")
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    output.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(output), "PNG"):
        raise RuntimeError(f"Unable to write icon: {output}")


def build_windows_icon() -> None:
    png = OUTPUT_DIR / "app-icon-1024.png"
    render_png(1024, png)
    with Image.open(png) as source:
        source.save(
            OUTPUT_DIR / "app-icon.ico",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )


def build_macos_icon() -> None:
    iconset = OUTPUT_DIR / "app-icon.iconset"
    mapping = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for filename, size in mapping.items():
        render_png(size, iconset / filename)
    subprocess.run(
        ["iconutil", "--convert", "icns", str(iconset), "--output", str(OUTPUT_DIR / "app-icon.icns")],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=("windows", "macos"))
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.platform == "windows":
        build_windows_icon()
    else:
        build_macos_icon()


if __name__ == "__main__":
    main()
