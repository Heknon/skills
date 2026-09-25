#!/bin/sh
# Renames users.email to users.email_address in the database named by --env.
# There is no down migration.
if [ "$1" != "--env" ] || [ -z "$2" ]; then
    echo "usage: migrate.sh --env <dev|staging|prod>" >&2
    exit 2
fi
echo "ALTER TABLE users RENAME COLUMN email TO email_address; -- on $2"
echo "(sandbox: nothing was executed)"
