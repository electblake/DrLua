Set-Location (Split-Path $PSScriptRoot -Parent)
$version = uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
$arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
$asset = "dist/drlua-v$version-windows-$arch.exe"
Copy-Item -LiteralPath "dist/drlua.exe" -Destination $asset
gh release create "v$version" $asset --repo electblake/DrLua --title "DrLua v$version" --notes-file README.md
