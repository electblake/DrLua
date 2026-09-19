#Requires -Version 7.0
param(
    [Parameter(Mandatory)]
    [string]$FfmpegRoot,
    [string]$IsccPath = "$env:LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
$version = (Select-String -Path pyproject.toml -Pattern '^version = "(.+)"$').Matches.Groups[1].Value
$artifact = "DrLua-$version-windows-amd64"

New-Item -ItemType Directory -Force build/vendor | Out-Null
Copy-Item -LiteralPath "$FfmpegRoot/bin/ffprobe.exe" -Destination build/vendor/ffprobe.exe
Copy-Item -LiteralPath "$FfmpegRoot/LICENSE" -Destination build/vendor/LICENSE
Copy-Item -LiteralPath "$FfmpegRoot/README.txt" -Destination build/vendor/README.txt
(Get-FileHash build/vendor/ffprobe.exe -Algorithm SHA256).Hash + '  ffprobe.exe' |
    Set-Content build/vendor/SHA256.txt

uv venv --clear build/installer-venv --python 3.12.9
uv export --locked --all-groups --no-emit-project --format requirements-txt --output-file build/installer-requirements.txt
uv pip sync --python build/installer-venv/Scripts/python.exe build/installer-requirements.txt
& build/installer-venv/Scripts/python.exe -I -m PyInstaller --clean --noconfirm scripts/DrLua.spec
& "dist/$artifact/drlua-cli.exe" . --version
& $IsccPath "/DAppVersion=$version" scripts/DrLua.iss
Get-FileHash "dist/$artifact-Setup.exe" -Algorithm SHA256
