# -*- mode: python ; coding: utf-8 -*-
import importlib.metadata

from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

datas, binaries, hiddenimports = [], [], []
for package in ("paddleocr", "paddlex", "onnxruntime", "pyclipper", "shapely"):
    try:
        package_datas, package_binaries, package_hidden = collect_all(package)
        datas += package_datas
        binaries += package_binaries
        hiddenimports += package_hidden
    except Exception:
        pass

hiddenimports += collect_submodules("paddleocr")

# PaddleX checks its optional OCR dependencies at runtime through
# importlib.metadata. PyInstaller does not include distribution metadata by
# default, so a packaged app would incorrectly report missing dependencies.
# Keep this aligned with PaddleX's official PyInstaller packaging guidance.
try:
    from paddlex.utils import deps as paddlex_deps

    installed_distributions = {
        dist.metadata["Name"] for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    }
    paddlex_dependencies = set(paddlex_deps.BASE_DEP_SPECS.keys())
    metadata_packages = installed_distributions & paddlex_dependencies
    metadata_packages.update({"paddlex", "paddleocr", "onnxruntime", "PyQt6"})
    for package in sorted(metadata_packages):
        try:
            datas += copy_metadata(package)
        except importlib.metadata.PackageNotFoundError:
            pass
except Exception as exc:
    raise RuntimeError("Unable to collect PaddleX dependency metadata") from exc

a = Analysis(
    ["../run_desktop.py"],
    pathex=["../src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "IPython", "jupyter", "matplotlib.tests"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PaddleOCRDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PaddleOCRDesktop",
)
app = BUNDLE(
    coll,
    name="PaddleOCR Desktop.app",
    bundle_identifier="com.atomnlp.paddleocr-desktop",
    info_plist={
        "CFBundleDisplayName": "PaddleOCR Desktop",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
    },
)
