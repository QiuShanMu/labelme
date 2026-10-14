"""Frozen-app entry point for the standalone labelme builds.

PyInstaller executes this module as ``__main__``. Keeping the launcher in a
separate file (rather than pointing PyInstaller at ``labelme/__main__.py``)
means multiprocessing children re-enter a tiny script instead of re-running the
whole CLI parser, and ``freeze_support()`` runs before any Qt import.
"""

from __future__ import annotations

import multiprocessing

from labelme.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
