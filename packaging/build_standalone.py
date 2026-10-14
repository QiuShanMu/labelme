"""Build the standalone (frozen) labelme application with PyInstaller.

The script is deliberately dependency-light so CI can run it with
``uv run --with pyinstaller`` on a runner that never installed the full dev
environment:

    uv run --python 3.12 --with 'pyinstaller>=6.10' \
        packaging/build_standalone.py --version 7.8.1

It is imported by the release workflow, which passes the tag-derived version.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGING_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGING_DIR.parent
APP_NAME = "labelme"
PRODUCT_NAME = "Labelme"
ORGANIZATION = "labelme"


def bundle_identifier(*, version: str) -> str:
    return f"io.labelme.labelme.{version}"


def write_config(*, version: str) -> Path:
    # labelme reads __version__ from importlib.metadata, so the editable install
    # in the build environment (a vcs-derived "7.8.2.dev0+g..." string) would
    # leak into the frozen app. Ship a canonical dist-info for the requested
    # version instead; the spec adds it and skips the real one.
    dist_info = PACKAGING_DIR / "_generated" / f"{APP_NAME}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(
        "\n".join(
            [
                "Metadata-Version: 2.1",
                f"Name: {APP_NAME}",
                f"Version: {version}",
                "Summary: Image annotation with Python.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    config = {
        "bundle_name": APP_NAME,
        "product_name": PRODUCT_NAME,
        "organization": ORGANIZATION,
        "version": version,
        "bundle_identifier": bundle_identifier(version=version),
        "dist_info_dir": str(dist_info),
    }
    config_path = PACKAGING_DIR / "pyinstaller_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path


def cleanup() -> None:
    (PACKAGING_DIR / "pyinstaller_config.json").unlink(missing_ok=True)
    shutil.rmtree(PACKAGING_DIR / "_generated", ignore_errors=True)


def build(*, version: str, clean: bool) -> Path:
    # The generated config/dist-info must not survive into the committed tree,
    # so they are removed again whether or not PyInstaller succeeds.
    write_config(version=version)
    try:
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--distpath",
            str(REPO_ROOT / "dist"),
            "--workpath",
            str(REPO_ROOT / "build"),
        ]
        if clean:
            cmd.append("--clean")
        cmd.append(str(PACKAGING_DIR / "labelme.spec"))

        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        print("+ " + " ".join(cmd), flush=True)
        subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=True)
    finally:
        cleanup()

    if sys.platform == "darwin":
        artifact = REPO_ROOT / "dist" / f"{APP_NAME}.app"
    elif os.name == "nt":
        artifact = REPO_ROOT / "dist" / APP_NAME / f"{APP_NAME}.exe"
    else:
        artifact = REPO_ROOT / "dist" / APP_NAME
    if not artifact.exists():
        raise SystemExit(f"Expected build artifact is missing: {artifact}")
    strip_foreign_metadata(artifact=artifact, version=version)
    return artifact


def strip_foreign_metadata(*, artifact: Path, version: str) -> None:
    """Remove any labelme dist-info other than the canonical one just built.

    PyInstaller auto-includes metadata for the editable install in the build
    environment (a vcs-derived "7.8.2.dev0+g..." string). On macOS that metadata
    is mirrored into Contents/Frameworks as symlinks, and a dangling symlink is
    discovered first by importlib.metadata, which then reports a None version.
    Both real directories and symlinks therefore have to go, which rules out
    shutil.rmtree alone (it refuses to unlink a symlink).
    """
    canonical = f"{APP_NAME}-{version}.dist-info"
    for path in sorted(artifact.rglob(f"{APP_NAME}-*.dist-info")):
        if path.name == canonical:
            continue
        if path.is_symlink() or os.path.isfile(path):
            path.unlink(missing_ok=True)
        else:
            shutil.rmtree(path, ignore_errors=True)
    kept = [p.relative_to(artifact) for p in artifact.rglob(f"{APP_NAME}-*.dist-info")]
    print(f"Kept metadata: {kept}", flush=True)


def verify(*, version: str) -> None:
    """Run the frozen binary's --version to prove package metadata survived.

    labelme reads ``__version__`` from importlib.metadata, so a bundle that
    dropped the ``labelme-*.dist-info`` directory would import fine but crash
    on startup. --version exits before any window is created, so this works
    headless (QT_QPA_PLATFORM=offscreen keeps Qt quiet on Linux CI).
    """
    if sys.platform == "darwin":
        binary = (
            REPO_ROOT / "dist" / f"{APP_NAME}.app" / "Contents" / "MacOS" / APP_NAME
        )
    elif os.name == "nt":
        binary = REPO_ROOT / "dist" / APP_NAME / f"{APP_NAME}.exe"
    else:
        binary = REPO_ROOT / "dist" / APP_NAME / APP_NAME

    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    proc = subprocess.run(
        [str(binary), "--version"],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    print(proc.stdout.strip(), proc.stderr.strip(), sep="\n", flush=True)
    expected = f"Labelme {version}"
    if proc.returncode != 0 or expected not in proc.stdout:
        raise SystemExit(
            f"Frozen app failed the version smoke test: expected {expected!r}, "
            f"got exit={proc.returncode} stdout={proc.stdout!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="build_standalone.py")
    parser.add_argument(
        "--version",
        required=True,
        help="version string baked into the bundle metadata (e.g. 7.8.1)",
    )
    parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="reuse PyInstaller's work directory instead of rebuilding from scratch",
    )
    parser.add_argument(
        "--no-verify",
        dest="verify",
        action="store_false",
        help="skip running the frozen binary's --version smoke test",
    )
    args = parser.parse_args()

    artifact = build(version=args.version, clean=args.clean)
    print(f"Built: {artifact}", flush=True)
    if args.verify:
        verify(version=args.version)
        print(f"Verified: {artifact}", flush=True)


if __name__ == "__main__":
    main()
