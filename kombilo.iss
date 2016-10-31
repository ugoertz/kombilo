; -- kombilo.iss --
; For Kombilo 0.8

[Setup]
AppName=Kombilo
AppVerName=Kombilo 0.8
AppCopyright=Copyright (C) 2001- Ulrich Goertz (ug@geometry.de)
AppPublisher=Ulrich Goertz
AppPublisherURL=http://www.u-go.net/
DefaultDirName={pf}\kombilo08
DefaultGroupName=Kombilo
UninstallDisplayIcon={app}\MyProg.exe
Compression=bzip
SourceDir=c:\projects\kombilo\dist\kombilo\
OutputDir=c:\projects\kombilo\installer\
OutputBaseFilename=kombilo08
MinVersion=6.0
AllowNoIcons=yes

[Files]
Source: "*"; DestDir: "{app}"; Flags: recursesubdirs

; [Run]
; Filename: {app}\vcredist_x86.exe; Parameters: "/q:a /c:""VCREDI~3.EXE /q:a /c:""""msiexec /i vcredist.msi /qb!"""""""; WorkingDir: {tmp}; StatusMsg: Installing Microsoft DLLs needed for Python; Flags: waituntilterminated;

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"

[Icons]
Name: "{group}\Kombilo"; Filename: "{app}\kombilo.exe"; WorkingDir: "{app}"; IconFilename: "{app}\kombilo.ico"
Name: "{group}\Uninstall Kombilo"; Filename: "{uninstallexe}";
Name: "{userdesktop}\Kombilo"; Filename: "{app}\kombilo.exe"; WorkingDir:"{app}"; Tasks: desktopicon; IconFilename: "{app}\kombilo.ico"

