$ErrorActionPreference = "Stop"

$AppRoot = Split-Path -Parent $PSScriptRoot
$env:EAP_SYSTEM_HOME = "D:\EAPSystem"
$env:EAP_DATA_DIR = "D:\EAPSystem\data"
$env:EAP_EXPORT_DIR = "D:\EAPSystem\exports"
$env:EAP_UPLOAD_DIR = "D:\EAPSystem\uploads"

Set-Location $AppRoot
& "$AppRoot\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
