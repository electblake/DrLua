#Requires -Version 7.0
param(
    [Parameter(Mandatory)]
    [string]$FfmpegRoot,
    [string]$IsccPath = "$env:LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
& "$PSScriptRoot/build-setup.ps1" -FfmpegRoot $FfmpegRoot -IsccPath $IsccPath
$version = (Select-String -Path pyproject.toml -Pattern '^version = "(.+)"$').Matches.Groups[1].Value
$asset = "dist/DrLua-$version-windows-amd64-Setup.exe"
$checksums = "dist/DrLua-$version-SHA256SUMS.txt"
(Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash.ToLowerInvariant() + '  ' + (Split-Path $asset -Leaf) |
    Set-Content -LiteralPath $checksums
$notes = "build/release-notes-$version.md"
((Get-Content CHANGELOG.md -Raw) -split "(?m)^## \[$([regex]::Escape($version))\] - [^\r\n]+", 2)[1].Split('## [')[0].Trim() |
    Set-Content -LiteralPath $notes
git tag -a "v$version" -m "DrLua v$version"
git push origin HEAD "refs/tags/v$version"
gh release create "v$version" $asset $checksums --repo electblake/DrLua --verify-tag --title "DrLua v$version" --notes-file $notes --latest
