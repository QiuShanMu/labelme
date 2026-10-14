# -*- mode: python ; coding: utf-8 -*-
"""Shared PyInstaller spec for the standalone labelme builds.

build_standalone.py generates a small JSON config next to this file before
invoking PyInstaller, so the packaging metadata (version, bundle id) and the
per-OS naming come from one place.

Scope notes:
- Linux produces a onedir directory consumed by build_appimage.sh; macOS and
  Windows ship an .app / .exe themselves.
- pyside6-deploy is intentionally not used: the pyproject ``project.name`` is
  ``labelme`` and Pyside6 deploy configs expect a valid, matching Python
  identifier package, so PyInstaller is the simpler, more explicit path here.
"""

import importlib.metadata
import json
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import copy_metadata

SPEC_DIR = Path(SPECPATH).resolve()  # noqa: F821  # injected by PyInstaller
REPO_ROOT = SPEC_DIR.parent
CONFIG = json.loads((SPEC_DIR / "pyinstaller_config.json").read_text())

BUNDLE_NAME = CONFIG["bundle_name"]
PRODUCT_NAME = CONFIG["product_name"]
VERSION = CONFIG["version"]

datas = []
binaries = []
hiddenimports = []

# labelme resolves its own __version__ through importlib.metadata, and so do
# several dependencies (gdown, osam, ...) at import time. PyInstaller does not
# ship dist-info directories by default, so the frozen app would raise
# PackageNotFoundError during startup. Copying every distribution's metadata
# costs a few hundred kilobytes and keeps all of them resolvable. The labelme
# entry itself is skipped: the build script supplies a canonical dist-info for
# the requested version, and the build environment's editable install would
# otherwise contribute a vcs-derived "7.8.2.dev0+g..." version.
generated_dist_info = Path(CONFIG["dist_info_dir"])
datas += [(str(generated_dist_info), generated_dist_info.name)]
for distribution in importlib.metadata.distributions():
    name = distribution.metadata["Name"]
    if not name or name == BUNDLE_NAME:
        continue
    try:
        datas += copy_metadata(name)
    except Exception:  # noqa: BLE001 -- metadata is absent for some build deps
        pass

# The labelme package ships its icons, translation catalogs, and the default
# config YAML as package data, and looks them up relative to __file__ at
# runtime, so they have to travel with the frozen app verbatim.
datas += collect_data_files("labelme")

# osam's YOLO-World tokenizer loads bpe_simple_vocab_16e6.txt.gz from its own
# package directory at import time; without it osam cannot even be imported.
datas += collect_data_files("osam")

# osam pulls onnxruntime and each model backend, which rely on dynamically
# imported submodules and shared libraries that static analysis cannot see.
# skimage/scipy expose compiled extensions (scipy.spatial's qhull in particular)
# that also need collect_all. matplotlib is declared in pyproject but never
# imported by the labelme runtime (only examples use it), so it is left out.
hiddenimports += collect_submodules("osam")
for package in ("onnxruntime", "skimage", "scipy"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

# Qt plugins (platform, imageformats, styles) and PySide6 runtime libraries.
for package in ("PySide6", "shiboken6"):
    binaries += collect_dynamic_libs(package)

# labelme only imports QtCore/QtGui/QtSvg/QtWidgets; the addons wheel carries
# hundreds of megabytes of QtWebEngine/QtQuick/Qt3D machinery that would only
# bloat the bundle.
excludes = [
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQml",
    "PySide6.Qt3DCore",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtMultimedia",
    "PySide6.QtPdf",
    "PySide6.QtWebSockets",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtPositioning",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtTest",
    "PySide6.QtSql",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtSpatialAudio",
    "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel",
    "PySide6.QtWebView",
    "tkinter",
]

a = Analysis(  # noqa: F821
    [str(SPEC_DIR / "entry_labelme.py")],
    pathex=[str(REPO_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[str(SPEC_DIR / "runtime_hook_labelme.py")],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

icon = "icon.ico" if os.name == "nt" else "icon-256.png"

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=BUNDLE_NAME,
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
    icon=str(REPO_ROOT / "labelme" / "icons" / icon),
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=BUNDLE_NAME,
)

# BUNDLE only exists on macOS; the Linux onedir output is wrapped into an
# AppImage by build_appimage.sh instead.
if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        coll,
        name=f"{BUNDLE_NAME}.app",
        icon=str(REPO_ROOT / "labelme" / "icons" / "icon-macos-512.png"),
        bundle_identifier=CONFIG["bundle_identifier"],
        version=VERSION,
        info_plist={
            "CFBundleName": PRODUCT_NAME,
            "CFBundleDisplayName": PRODUCT_NAME,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
            "LSApplicationCategoryType": "public.app-category.developer-tools",
        },
    )
