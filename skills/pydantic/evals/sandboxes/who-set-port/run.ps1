# Starts the API the way the team does on Windows.
$env:API_PORT = "8080"
uv run python -m api.main
