# Build AAL.exe and AalMcp.exe into dist/
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Missing .venv. Run: python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"
}

& $py -m PyInstaller --noconfirm --clean --distpath dist --workpath build aal.spec
& $py -m PyInstaller --noconfirm --clean --distpath dist --workpath build mcp_fs.spec

Write-Host "Done. Output: dist\AAL.exe and dist\AalMcp.exe (keep both in the same folder)."
