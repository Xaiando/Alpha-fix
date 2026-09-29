Option Explicit
Dim shell, fs, root, python
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
python = fs.BuildPath(root, ".venv\Scripts\pythonw.exe")
shell.CurrentDirectory = root
If Not fs.FileExists(python) Then
    MsgBox "Run Setup.bat in this folder first.", 48, "Alpha Fix"
Else
    shell.Run Chr(34) & python & Chr(34) & " -m alpha_fix --gui", 0, False
End If
