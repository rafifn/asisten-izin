#!/bin/sh
# Applies pending migrations (idempotent), then runs the given command.
set -e
python -m app.db
exec "$@"
