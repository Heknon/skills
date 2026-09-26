#!/bin/sh
# Run on the connected build server (Linux), then copy wheelhouse/ across
# on the transfer drive to the Windows build machine.
set -e
python3 -m pip download -r requirements.txt -d wheelhouse
