#!/bin/sh
# Starts the API the way the team does on Linux.
export API_PORT=8080
uv run python -m api.main
