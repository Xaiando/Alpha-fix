# PowerShell script to automate building Alpha Fix standalone executables and installer
$ErrorActionPreference = "Stop"

# Set working directory to the directory of this script (install/)
Set-Location $PSScriptRoot
$rootDir = Split-Path -Parent $PSScriptRoot

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "Starting Alpha Fix Installer Packaging Process" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Step 1: Ensure PyInstaller is installed in the virtual environment
Write-Host "`n[1/5] Checking PyInstaller installation..." -ForegroundColor Yellow
$pyinstallerInVenv = Join-Path $rootDir ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyinstallerInVenv)) {
    Write-Host "PyInstaller not found in .venv. Installing via uv..." -ForegroundColor Cyan
    Push-Location $rootDir
    uv pip install pyinstaller
    Pop-Location
    if (-not (Test-Path $pyinstallerInVenv)) {
        throw "Failed to install PyInstaller into .venv."
    }
}
Write-Host "PyInstaller is ready." -ForegroundColor Green

# Step 2: Check for Inno Setup compiler (ISCC)
Write-Host "`n[2/5] Checking for Inno Setup compiler (ISCC.exe)..." -ForegroundColor Yellow
$isccPath = ""
$possiblePaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $isccPath = $path
        break
    }
}

if ($isccPath -eq "") {
    Write-Host "Inno Setup not found in standard directories. Searching PATH..." -ForegroundColor Cyan
    $isccInPath = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($isccInPath) {
        $isccPath = $isccInPath.Source
    } else {
        Write-Host "Inno Setup is missing. Installing via winget..." -ForegroundColor Cyan
        & winget install --id JRSoftware.InnoSetup --exact --silent --accept-source-agreements --accept-package-agreements
        
        # Check all possible paths again
        foreach ($path in $possiblePaths) {
            if (Test-Path $path) {
                $isccPath = $path
                break
            }
        }
        
        if ($isccPath -eq "") {
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $isccInPath2 = Get-Command iscc.exe -ErrorAction SilentlyContinue
            if ($isccInPath2) {
                $isccPath = $isccInPath2.Source
            } else {
                throw "Inno Setup was installed but ISCC.exe could not be found. Please restart terminal or add Inno Setup to PATH."
            }
        }
    }
}
Write-Host "Inno Setup compiler is ready: $isccPath" -ForegroundColor Green

# Step 3: Run PyInstaller to build Production standalone executable
Write-Host "`n[3/5] Compiling Alpha Fix Production executable..." -ForegroundColor Yellow
Write-Host "Running PyInstaller on run_production.py..." -ForegroundColor Cyan
& $pyinstallerInVenv --onefile --clean --paths="$rootDir" --name="AlphaFix" run_production.py

if (-not (Test-Path "dist\AlphaFix.exe")) {
    throw "Production compilation failed. dist\AlphaFix.exe was not created."
}
Write-Host "Production executable compiled successfully at dist\AlphaFix.exe" -ForegroundColor Green

# Step 4: Run PyInstaller to build Sandbox standalone executable
Write-Host "`n[4/5] Compiling Alpha Fix Sandbox executable..." -ForegroundColor Yellow
Write-Host "Running PyInstaller on run_sandbox.py..." -ForegroundColor Cyan
& $pyinstallerInVenv --onefile --clean --paths="$rootDir" --name="AlphaFixSandbox" run_sandbox.py

if (-not (Test-Path "dist\AlphaFixSandbox.exe")) {
    throw "Sandbox compilation failed. dist\AlphaFixSandbox.exe was not created."
}
Write-Host "Sandbox executable compiled successfully at dist\AlphaFixSandbox.exe" -ForegroundColor Green

# Step 5: Run Inno Setup Compiler (ISCC) to build the setup wizard
Write-Host "`n[5/5] Compiling setup wizard using Inno Setup..." -ForegroundColor Yellow
Write-Host "Running ISCC on installer.iss..." -ForegroundColor Cyan
& $isccPath installer.iss

if (-not (Test-Path "dist\AlphaFixSetup.exe")) {
    throw "Setup wizard compilation failed. dist\AlphaFixSetup.exe was not created."
}
Write-Host "Setup wizard compiled successfully at dist\AlphaFixSetup.exe" -ForegroundColor Green

# Step 6: Clean up build directories and .spec files
Write-Host "`nCleaning up build artifacts..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
}
if (Test-Path "AlphaFix.spec") {
    Remove-Item "AlphaFix.spec" -Force
}
if (Test-Path "AlphaFixSandbox.spec") {
    Remove-Item "AlphaFixSandbox.spec" -Force
}

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host "Process completed successfully!" -ForegroundColor Green
Write-Host "Installer is available at: install\dist\AlphaFixSetup.exe" -ForegroundColor Green
Write-Host "Standalone executables are at: install\dist\AlphaFix.exe, install\dist\AlphaFixSandbox.exe" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
