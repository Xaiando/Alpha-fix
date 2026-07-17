# PowerShell script to build Alpha Fix Sandbox as a single .exe installer
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
$rootDir = Split-Path -Parent $PSScriptRoot

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Alpha Fix Sandbox - Installer Build" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Step 1: Ensure PyInstaller is available in the venv
Write-Host "`n[1/4] Checking PyInstaller..." -ForegroundColor Yellow
$pyinstallerInVenv = Join-Path $rootDir ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyinstallerInVenv)) {
    Write-Host "PyInstaller not found. Installing via uv..." -ForegroundColor Cyan
    Push-Location $rootDir
    uv pip install pyinstaller
    Pop-Location
    if (-not (Test-Path $pyinstallerInVenv)) {
        throw "Failed to install PyInstaller."
    }
}
Write-Host "PyInstaller ready: $pyinstallerInVenv" -ForegroundColor Green

# Step 2: Find Inno Setup compiler
Write-Host "`n[2/4] Locating Inno Setup compiler (ISCC.exe)..." -ForegroundColor Yellow
$isccPath = ""
$possiblePaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
foreach ($p in $possiblePaths) {
    if (Test-Path $p) { $isccPath = $p; break }
}
if ($isccPath -eq "") {
    $found = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($found) {
        $isccPath = $found.Source
    } else {
        Write-Host "Inno Setup not found. Installing via winget..." -ForegroundColor Cyan
        & winget install --id JRSoftware.InnoSetup --exact --silent --accept-source-agreements --accept-package-agreements
        foreach ($p in $possiblePaths) {
            if (Test-Path $p) { $isccPath = $p; break }
        }
        if ($isccPath -eq "") {
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $found2 = Get-Command iscc.exe -ErrorAction SilentlyContinue
            if ($found2) { $isccPath = $found2.Source }
            else { throw "ISCC.exe not found after install. Add Inno Setup to PATH and retry." }
        }
    }
}
Write-Host "Inno Setup ready: $isccPath" -ForegroundColor Green

# Step 3: PyInstaller - build sandbox only, windowless (no console)
Write-Host "`n[3/4] Compiling AlphaFixSandbox.exe with PyInstaller..." -ForegroundColor Yellow

# Clean old build artifacts first
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "AlphaFixSandbox.spec") { Remove-Item "AlphaFixSandbox.spec" -Force }
if (Test-Path "dist\AlphaFixSandbox.exe") { Remove-Item "dist\AlphaFixSandbox.exe" -Force }

& $pyinstallerInVenv `
    --onefile `
    --clean `
    --noconsole `
    --paths="$rootDir" `
    --hidden-import="alpha_fix_2.gui" `
    --hidden-import="alpha_fix_2.pipeline" `
    --hidden-import="alpha_fix_2.service" `
    --hidden-import="alpha_fix_2.config" `
    --hidden-import="alpha_fix_2.radfield" `
    --hidden-import="alpha_fix.samples" `
    --hidden-import="cv2" `
    --name="AlphaFixSandbox" `
    run_sandbox.py

if (-not (Test-Path "dist\AlphaFixSandbox.exe")) {
    throw "PyInstaller failed. dist\AlphaFixSandbox.exe was not created."
}
$exeSize = [math]::Round((Get-Item "dist\AlphaFixSandbox.exe").Length / 1MB, 1)
Write-Host "Compiled successfully: dist\AlphaFixSandbox.exe ($exeSize MB)" -ForegroundColor Green

# Step 4: Inno Setup - wrap in a single setup wizard
Write-Host "`n[4/4] Building installer with Inno Setup..." -ForegroundColor Yellow
& $isccPath installer_sandbox.iss

if (-not (Test-Path "dist\AlphaFixSandboxSetup.exe")) {
    throw "Inno Setup failed. dist\AlphaFixSandboxSetup.exe was not created."
}
$setupSize = [math]::Round((Get-Item "dist\AlphaFixSandboxSetup.exe").Length / 1MB, 1)
Write-Host "Installer built: dist\AlphaFixSandboxSetup.exe ($setupSize MB)" -ForegroundColor Green

# Cleanup
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "AlphaFixSandbox.spec") { Remove-Item "AlphaFixSandbox.spec" -Force }

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "  Done!" -ForegroundColor Green
Write-Host "  Installer: install\dist\AlphaFixSandboxSetup.exe" -ForegroundColor Green
Write-Host "  Standalone: install\dist\AlphaFixSandbox.exe" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
