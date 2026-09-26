<#
Run one command N times, each with a time limit and an empty stdin, count
the failures, and keep the output of the first failure.

Usage, from the project root:
    .\run_n.ps1 -Times 20 -TimeoutSeconds 60 -- uv run python repro_race.py

A run fails when its exit code is not 0 or it hits the time limit (it is
then stopped, with its child processes). Stdin is an empty file, so a
forgotten breakpoint() or input() ends at once instead of waiting.

Prints one line per run and a summary such as "7 of 20 failed".
The first failing run's stdout and stderr are kept in
run_n-first-failure.txt in the temporary folder (the summary prints the
path), so nothing is left in the project. The script's own exit code is
the failure count (0 when every run passed).
#>
param(
    [Parameter(Mandatory = $true)][int]$Times,
    [int]$TimeoutSeconds = 60,
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Command
)

if ($Command[0] -eq "--") { $Command = $Command[1..($Command.Length - 1)] }
$exe = $Command[0]
$argList = @()
if ($Command.Length -gt 1) { $argList = $Command[1..($Command.Length - 1)] }

$stdin = New-TemporaryFile
$out = New-TemporaryFile
$err = New-TemporaryFile
$kept = Join-Path ([System.IO.Path]::GetTempPath()) "run_n-first-failure.txt"
$failures = 0

for ($i = 1; $i -le $Times; $i++) {
    $start = @{
        FilePath               = $exe
        NoNewWindow            = $true
        PassThru               = $true
        RedirectStandardInput  = $stdin.FullName
        RedirectStandardOutput = $out.FullName
        RedirectStandardError  = $err.FullName
    }
    if ($argList.Count -gt 0) { $start.ArgumentList = $argList }
    $p = Start-Process @start
    $null = $p.Handle  # keep the handle, so ExitCode is readable afterwards
    if ($p.WaitForExit($TimeoutSeconds * 1000)) {
        $p.WaitForExit()
        $code = $p.ExitCode
        $result = "exit $code"
    } else {
        $p.Kill($true)  # PowerShell 7: also stops child processes
        $p.WaitForExit()
        $code = "timeout"
        $result = "timed out after $TimeoutSeconds s"
    }
    if ($code -ne 0) {
        $failures++
        if ($failures -eq 1) {
            "run $i of ${Times}: $result" | Set-Content $kept
            "--- stdout" | Add-Content $kept
            Get-Content $out.FullName | Add-Content $kept
            "--- stderr" | Add-Content $kept
            Get-Content $err.FullName | Add-Content $kept
        }
    }
    "run ${i}: $result"
}

Remove-Item $stdin.FullName, $out.FullName, $err.FullName
"$failures of $Times failed"
if ($failures -gt 0) { "first failure kept in $kept" }
exit $failures
