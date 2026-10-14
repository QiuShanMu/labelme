"""PyInstaller runtime hook: pin the frozen app's resource layout.

Collected package data lands in the app bundle unter ``_internal`` (onedir /
macOS) or next to the executable (onefile). labelme resolves icons, translation
catalogs, and the default config relative to ``labelme.__file__``, which works
once the whole ``labelme`` package tree is collected. This hook only hardens the
environment flags that differ in a frozen build.
"""

import os
import sys

# Qt reads its plugin path from its own prefix; quarantine/codesign variations
# on macOS can otherwise resolve a stale system Qt.
os.environ.setdefault("QT_API", "pyside6")

# Keep pyside6-deploy style "one process per plugin" surprises away: labelme is
# a plain desktop app and multiprocessing is only used for model downloads.
if sys.platform == "darwin":
    os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")
