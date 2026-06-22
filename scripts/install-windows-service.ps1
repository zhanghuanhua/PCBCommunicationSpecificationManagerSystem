$ErrorActionPreference = "Stop"

$ServiceName = "EAPSpecManager"
$DisplayName = "EAP Spec Manager"
$AppRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $AppRoot "scripts\start-server.ps1"

if (-not (Test-Path $StartScript)) {
    throw "启动脚本不存在：$StartScript"
}

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

$command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
New-Service -Name $ServiceName -DisplayName $DisplayName -BinaryPathName $command -StartupType Automatic
Start-Service -Name $ServiceName

Write-Host "服务已安装并启动：$DisplayName"
Write-Host "访问地址：http://服务器IP:8000"
