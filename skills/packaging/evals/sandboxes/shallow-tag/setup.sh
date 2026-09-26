#!/bin/sh
# Turns this folder into the repository as the developer has it: one
# commit, tagged v1.4.0. Run once from this folder: sh setup.sh
set -e
git init -q -b main
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m "Release 1.4.0"
git -c user.name=dev -c user.email=dev@example.com tag -a v1.4.0 -m "Release 1.4.0"
git describe --tags
