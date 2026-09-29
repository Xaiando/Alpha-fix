$ErrorActionPreference = 'Stop'
$alphaProjectRoot = Split-Path -Parent $PSScriptRoot
$alphaPython = Join-Path $alphaProjectRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $alphaPython)) {
    throw 'Run Setup.bat to install the environment first.'
}
$alphaShell = New-Object -ComObject WScript.Shell
$alphaShortcut = $alphaShell.CreateShortcut((Join-Path $alphaProjectRoot 'Alpha Fix.lnk'))
$alphaShortcut.TargetPath = $alphaPython
$alphaShortcut.Arguments = '-m alpha_fix --gui'
$alphaShortcut.WorkingDirectory = $alphaProjectRoot
$alphaShortcut.Description = 'Alpha Fix 3 - video and image alpha cleanup'
$alphaIcon = Join-Path $alphaProjectRoot 'src\alpha_fix\assets\alpha-fix.ico'
if (Test-Path -LiteralPath $alphaIcon) {
    $alphaShortcut.IconLocation = $alphaIcon
}
$alphaShortcut.Save()
Write-Output 'Created Alpha Fix.lnk in the project folder.'
