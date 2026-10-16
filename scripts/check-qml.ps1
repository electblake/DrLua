#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force build/qml/DrLua | Out-Null
Set-Content build/qml/DrLua/qmldir "module DrLua`ntypeinfo drlua.qmltypes"
uv run pyside6-metaobjectdump -o build/drlua-metatypes.json drlua/ui/form.py drlua/ui/controller.py
uv run pyside6-qmltyperegistrar --import-name DrLua --major-version 1 --minor-version 0 --generate-qmltypes build/qml/DrLua/drlua.qmltypes -o build/drlua_qmltypes.cpp build/drlua-metatypes.json
$qmlImports = uv run python -c 'from PySide6.QtCore import QLibraryInfo; print(QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath))'
$qmlFiles = (Get-ChildItem drlua/ui/qml -Filter '*.qml').FullName
uv run pyside6-qmllint --json build/qml-lint.json -W 0 -I build/qml -I $qmlImports $qmlFiles
