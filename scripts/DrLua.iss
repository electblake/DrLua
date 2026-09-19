#define AppName "DrLua"
#define Artifact "DrLua-" + AppVersion + "-windows-amd64"

[Setup]
AppId=electblake.DrLua
AppMutex=electblake.DrLua.Running
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=electblake
AppPublisherURL=https://github.com/electblake/DrLua
DefaultDirName={localappdata}\Programs\DrLua
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
OutputDir=..\dist
OutputBaseFilename={#Artifact}-Setup
UninstallDisplayIcon={app}\DrLua.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
SetupLogging=yes

[Files]
Source: "..\dist\{#Artifact}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{autoprograms}\DrLua"; Filename: "{app}\DrLua.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\DrLua"; Filename: "{app}\DrLua.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\DrLua.exe"; Description: "{cm:LaunchProgram,DrLua}"; Flags: nowait postinstall skipifsilent

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if CheckForMutexes('electblake.DrLua.Running') then
    Result := 'Please close all DrLua windows before continuing setup.';
end;
