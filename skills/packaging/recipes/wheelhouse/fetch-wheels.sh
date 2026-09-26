#!/bin/sh
# Recipe: the connected side of a wheelhouse. A person runs it on a machine
# that can reach the public index, with requirements.txt carried out from
# the air-gapped side, then carries wheelhouse/ back in.
# Ran on Linux with pip 26.2.1 for a win_amd64 / CPython 3.12 target; the
# offline install it feeds ran on Linux (see README.md; not run on Windows).
# Change: TARGET_PLATFORM, TARGET_PYTHON, BACKEND (the build-system
# requirement, only if the project is built on the air-gapped side).
set -eu
TARGET_PLATFORM="${TARGET_PLATFORM:-win_amd64}"   # manylinux_2_17_x86_64 for Linux
TARGET_PYTHON="${TARGET_PYTHON:-3.12}"
BACKEND="${BACKEND:-hatchling==1.32.4}"

# Wheels only, for the target platform and Python; never sdists, which
# would need a compiler on the other side.
python3 -m pip download -r requirements.txt -d wheelhouse \
    --only-binary=:all: --platform "$TARGET_PLATFORM" \
    --python-version "$TARGET_PYTHON" --implementation cp

python3 -m pip download "$BACKEND" -d wheelhouse \
    --only-binary=:all: --platform "$TARGET_PLATFORM" \
    --python-version "$TARGET_PYTHON" --implementation cp

ls wheelhouse
