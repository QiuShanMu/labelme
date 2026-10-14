#!/usr/bin/env bash
# Wrap the PyInstaller onedir output into a Linux AppImage.
#
# Usage: packaging/build_appimage.sh <version>
set -euo pipefail

version="${1:?usage: build_appimage.sh <version>}"
app_name="labelme"

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

appdir="dist/${app_name}.AppDir"
rm -rf "$appdir"

if [[ ! -d "dist/${app_name}" ]]; then
  echo "dist/${app_name} not found; run build_standalone.py first" >&2
  exit 1
fi

# AppDir layout expected by AppRun.
mkdir -p "$appdir/usr/bin" "$appdir/usr/share/applications" "$appdir/usr/share/icons/hicolor/256x256/apps"
cp -a "dist/${app_name}/." "$appdir/usr/bin/"
cp "packaging/labelme.desktop" "$appdir/${app_name}.desktop"
cp "packaging/labelme.desktop" "$appdir/usr/share/applications/${app_name}.desktop"
cp "labelme/icons/icon-256.png" "$appdir/${app_name}.png"
cp "labelme/icons/icon-256.png" "$appdir/usr/share/icons/hicolor/256x256/apps/${app_name}.png"

# AppRun selects the target, then execs the frozen binary with the user's args.
cat > "$appdir/AppRun" <<'EOF'
#!/usr/bin/env bash
set -eu
here="$(dirname "$(readlink -f "$0")")"
export LD_LIBRARY_PATH="$here/usr/bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="$here/usr/bin/PySide6/Qt/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
exec "$here/usr/bin/labelme" "$@"
EOF
chmod +x "$appdir/AppRun"

# appimagetool is a static binary; keep the download out of the repo.
tool_dir="${RUNNER_TEMP:-/tmp}/appimagetool"
tool="$tool_dir/appimagetool-x86_64.AppImage"
if [[ ! -x "$tool" ]]; then
  mkdir -p "$tool_dir"
  curl -sSL --retry 3 -o "$tool" \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x "$tool"
fi

# runner-images has FUSE, but --appimage-extract-and-run keeps this working in
# containers and on hosts without /dev/fuse.
export ARCH=x86_64
export VERSION="$version"
out="dist/${app_name}-${version}-x86_64.AppImage"
"$tool" --appimage-extract-and-run --no-appstream "$appdir" "$out"
chmod +x "$out"

echo "Built: $out"
