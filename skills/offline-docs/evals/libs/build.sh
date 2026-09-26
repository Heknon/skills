#!/bin/sh
# Rebuilds the made-up libraries' wheels (and sdists) and copies each into
# the sandboxes that install it. Needs uv 0.12 and uv_build from an index.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
out="$here/dist"
rm -rf "$out"
for lib in "$here"/*/; do
  uv build -q --out-dir "$out" "$lib"
done
sb="$here/../sandboxes"
cp "$out/fetchkit-2.0.0-py3-none-any.whl" "$sb/vendored-copy/wheels/"
cp "$out/fetchkit-2.0.0-py3-none-any.whl" "$sb/kwargs-passthrough/wheels/"
cp "$out/fetchkit-2.0.0-py3-none-any.whl" "$out/types_fetchkit-1.6.0.20260101-py3-none-any.whl" "$sb/stub-mismatch/wheels/"
cp "$out/fetchkit-1.4.0-py3-none-any.whl" "$out/fetchkit-1.5.0-py3-none-any.whl" "$out/fetchkit-1.5.0.tar.gz" "$sb/what-changed/wheels/"
cp "$out/callagain-0.9.0-py3-none-any.whl" "$sb/stale-docstring/wheels/"
cp "$out/quickcfg-3.1.0-py3-none-any.whl" "$sb/no-such-option/wheels/"
cp "$out/reportjob-1.0.0-py3-none-any.whl" "$sb/import-side-effect/wheels/"
rm -rf "$out"
echo "wheels copied into $sb"
