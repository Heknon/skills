# Not run on Windows. Puts an older ruff (0.6.9) first on PATH for this
# terminal, the way a global install shadows the project's ruff.
$dir = Join-Path $env:LOCALAPPDATA 'offline-docs-old-ruff'
uv venv -q $dir
uv pip install -q --python (Join-Path $dir 'Scripts\python.exe') ruff==0.6.9
$env:PATH = (Join-Path $dir 'Scripts') + ';' + $env:PATH
