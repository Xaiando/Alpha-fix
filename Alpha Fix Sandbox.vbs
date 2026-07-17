Option Explicit

Dim shell
Dim fso
Dim root
Dim pythonw
Dim command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    MsgBox "Alpha Fix Sandbox is not installed in the local .venv yet." & vbCrLf & _
        "Run 'uv sync' in this folder first.", vbExclamation, "Alpha Fix Sandbox"
    WScript.Quit 1
End If

shell.CurrentDirectory = root
command = """" & pythonw & """ -m alpha_fix_2.cli --gui"
shell.Run command, 1, False
