#!/usr/bin/env bash
# Package the PyInstaller .app into a distributable .dmg.
#
# Usage: packaging/build_dmg.sh <version>
#
# The .dmg is left unsigned; distribution to end users requires an Apple
# Developer ID signature plus notarization, which needs repository secrets that
# are out of scope here. Gatekeeper therefore shows the "unidentified developer"
# prompt on first launch.
set -euo pipefail

version="${1:?usage: build_dmg.sh <version>}"
app_name="labelme"

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

app="dist/${app_name}.app"
if [[ ! -d "$app" ]]; then
  echo "$app not found; run build_standalone.py first" >&2
  exit 1
fi

case "$(uname -m)" in
  arm64) arch="arm64" ;;
  x86_64) arch="x86_64" ;;
  *) arch="$(uname -m)" ;;
esac

staging="dist/dmg-staging"
rm -rf "$staging"
mkdir -p "$staging"
cp -R "$app" "$staging/"
ln -s /Applications "$staging/Applications"

out="dist/${app_name}-${version}-macos-${arch}.dmg"
rm -f "$out"
export VOLUME_NAME="Labelme ${version}"
hdiutil create \
  -volname "Labelme ${version}" \
  -srcfolder "$staging" \
  -ov -format UDZO \
  "$out"
rm -rf "$staging"

echo "Built: $out"
