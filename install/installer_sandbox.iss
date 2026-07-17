[Setup]
AppName=Alpha Fix Sandbox
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\Alpha Fix Sandbox
DefaultGroupName=Alpha Fix Sandbox
UninstallDisplayIcon={app}\AlphaFixSandbox.exe
OutputDir=dist
OutputBaseFilename=AlphaFixSandboxSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\AlphaFixSandbox.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\Alpha Fix Sandbox"; Filename: "{app}\AlphaFixSandbox.exe"
Name: "{userdesktop}\Alpha Fix Sandbox"; Filename: "{app}\AlphaFixSandbox.exe"

[Run]
Filename: "{app}\AlphaFixSandbox.exe"; Description: "Launch Alpha Fix Sandbox"; Flags: postinstall nowait skipifsilent
