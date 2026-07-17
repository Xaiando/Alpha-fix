$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $root ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $pythonw)) {
    throw "Missing $pythonw. Run 'uv sync' in this folder first."
}

$shell = New-Object -ComObject WScript.Shell

$definitions = @(
    @{
        Shortcut = Join-Path $root "Alpha Fix.lnk"
        Target = $pythonw
        Arguments = "-m alpha_fix.cli --gui"
        Description = "Launch Alpha Fix production app"
    },
    @{
        Shortcut = Join-Path $root "Alpha Fix Sandbox.lnk"
        Target = $pythonw
        Arguments = "-m alpha_fix_2.cli --gui"
        Description = "Launch Alpha Fix sandbox app"
    }
)

foreach ($item in $definitions) {
    if (Test-Path $item.Shortcut) {
        Remove-Item $item.Shortcut -Force
    }
    $shortcut = $shell.CreateShortcut($item.Shortcut)
    $shortcut.TargetPath = $item.Target
    $shortcut.Arguments = $item.Arguments
    $shortcut.WorkingDirectory = $root
    $shortcut.IconLocation = "$pythonw,0"
    $shortcut.Description = $item.Description
    $shortcut.Save()
}

Write-Host "Created shortcuts in $root"
