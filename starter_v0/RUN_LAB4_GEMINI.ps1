
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python scripts/validate_submission.py
python scripts/run_full_lab.py
