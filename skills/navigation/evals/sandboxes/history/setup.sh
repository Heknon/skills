#!/bin/sh
# Builds the git history this scenario needs. Run once in the copied sandbox.
set -e
mkdir -p app
git init -q
git config user.email dev@example.com
git config user.name "Dana Levi"
printf 'MAX_RETRIES = 5\nTIMEOUT = 10\n' > app/net.py
git add app/net.py
git commit -qm "Add network settings"
printf 'MAX_RETRIES = 5\nTIMEOUT = 15\n' > app/net.py
git commit -qam "Raise timeout for slow partners"
git config user.name "Omer Katz"
printf 'MAX_RETRIES = 3\nTIMEOUT = 15\n' > app/net.py
git commit -qam "Lower retries: the gateway rate limits after 4 attempts (INC-212)"
printf 'MAX_RETRIES = 3\nTIMEOUT = 15\nBACKOFF = 2\n' > app/net.py
git commit -qam "Add backoff factor"
rm setup.sh
