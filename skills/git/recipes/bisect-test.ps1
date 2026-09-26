# A test script for `git bisect run` that runs one pytest file.
# Copy it outside the repository, edit $Module and $Test, then:
#   git bisect run pwsh -NoProfile -File ../bisect-test.ps1
# (powershell -NoProfile -File ... for Windows PowerShell 5.1)
# 0 good, 1 bad, 125 skip (cannot import, or pytest could not run the test).
# Written from bisect-test.sh; not run on Windows.
$Module = 'shop.money'
$Test = 'tests/test_money.py'

uv run --no-sync python -c "import $Module" *> $null
if ($LASTEXITCODE -ne 0) { exit 125 }
uv run --no-sync python -m pytest -x -q $Test *> $null
switch ($LASTEXITCODE) {
    0 { exit 0 }      # passed
    1 { exit 1 }      # a test failed
    default { exit 125 }  # 2 interrupted or collection error, 4 usage, 5 no tests
}
