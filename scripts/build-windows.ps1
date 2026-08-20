$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $ProjectDir

$BuildVenv = ".venv-build-py312"
$BuildPython = "$BuildVenv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $BuildPython)) {
    $PythonCommand = $null
    $PythonPrefixArgs = @()
    if (Get-Command python3.12 -ErrorAction SilentlyContinue) {
        $PythonCommand = "python3.12"
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonCommand = "python"
    }
    elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonCommand = "py"
        $PythonPrefixArgs = @("-3.12")
    }
    else {
        throw "Python 3.12 was not found. Install Python 3.12, enable Add Python to PATH, and run this script again."
    }

    $PythonVersion = & $PythonCommand @PythonPrefixArgs -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
    if ($LASTEXITCODE -ne 0 -or $PythonVersion.Trim() -ne "3.12") {
        throw "The detected Python command is version $PythonVersion. Python 3.12 is required."
    }
    Write-Host "Using $PythonCommand with Python $PythonVersion"
    & $PythonCommand @PythonPrefixArgs -m venv $BuildVenv
}
& $BuildPython -m pip install --upgrade pip setuptools wheel
& $BuildPython -m pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip
& $BuildPython -m pip install -e . pyinstaller pytest
& $BuildPython -m pytest
& $BuildPython scripts\generate-icons.py windows
& $BuildPython -m PyInstaller --noconfirm --clean build\desktop.spec

$Candidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)
$Compiler = $Candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $Compiler) {
    throw "Inno Setup 6 was not found. Install it and run this script again."
}
$CompilerDirectory = Split-Path -Parent $Compiler
$ChineseMessages = Join-Path $CompilerDirectory "Languages\ChineseSimplified.isl"
if (Test-Path -LiteralPath $ChineseMessages) {
    Write-Host "Using the Simplified Chinese installer language."
    & $Compiler "/DUseChineseLanguage" build\windows\installer.iss
}
else {
    Write-Warning "ChineseSimplified.isl was not found; building the installer with Inno Setup's built-in English language."
    & $Compiler build\windows\installer.iss
}
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE. See the compiler output above."
}
Write-Host "Installer created in the dist-installer directory."
