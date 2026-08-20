$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $ProjectDir

$BuildVenv = ".venv-build-py312"
$BuildPython = "$BuildVenv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $BuildPython)) {
    py -3.12 -m venv $BuildVenv
}
& $BuildPython -m pip install --upgrade pip setuptools wheel
& $BuildPython -m pip install -e . pyinstaller pytest
& $BuildPython -m pytest
& $BuildPython -m PyInstaller --noconfirm --clean build\desktop.spec

$Candidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)
$Compiler = $Candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $Compiler) {
    throw "Inno Setup 6 was not found. Install it and run this script again."
}
& $Compiler build\windows\installer.iss
Write-Host "Installer created in the dist-installer directory."
