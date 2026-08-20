$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $ProjectDir

if (-not (Test-Path ".venv-build\Scripts\python.exe")) {
    py -3.11 -m venv .venv-build
}
& .venv-build\Scripts\python.exe -m pip install --upgrade pip wheel
& .venv-build\Scripts\python.exe -m pip install -e . pyinstaller pytest
& .venv-build\Scripts\python.exe -m pytest
& .venv-build\Scripts\python.exe -m PyInstaller --noconfirm --clean build\desktop.spec

$Candidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)
$Compiler = $Candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $Compiler) {
    throw "未找到 Inno Setup 6。安装后重新运行本脚本。"
}
& $Compiler build\windows\installer.iss
Write-Host "安装包位于 dist-installer 目录。"
