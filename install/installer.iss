[Setup]
AppName=Alpha Fix
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\Alpha Fix
DefaultGroupName=Alpha Fix
UninstallDisplayIcon={app}\AlphaFix.exe
OutputDir=dist
OutputBaseFilename=AlphaFixSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\AlphaFix.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\AlphaFixSandbox.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\Alpha Fix"; Filename: "{app}\AlphaFix.exe"; Parameters: "--gui"
Name: "{group}\Alpha Fix Sandbox"; Filename: "{app}\AlphaFixSandbox.exe"; Parameters: "--gui"
Name: "{userdesktop}\Alpha Fix"; Filename: "{app}\AlphaFix.exe"; Parameters: "--gui"
Name: "{userdesktop}\Alpha Fix Sandbox"; Filename: "{app}\AlphaFixSandbox.exe"; Parameters: "--gui"

[Run]
Filename: "{app}\AlphaFix.exe"; Parameters: "--gui"; Description: "Launch Alpha Fix Production"; Flags: postinstall nowait skipifsilent unchecked
Filename: "{app}\AlphaFixSandbox.exe"; Parameters: "--gui"; Description: "Launch Alpha Fix Sandbox"; Flags: postinstall nowait skipifsilent unchecked
