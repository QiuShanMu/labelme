; Inno Setup script for the standalone Windows build.
;
; Built from the repository root with:
;   ISCC.exe /DAppVersion=7.8.1 /DDistPath=<abs>\dist /DArchSuffix=x86_64 packaging\labelme.iss
;
; Expects the PyInstaller onedir output at <DistPath>\labelme\labelme.exe.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef DistPath
  #define DistPath "..\dist"
#endif
#ifndef ArchSuffix
  #define ArchSuffix "x86_64"
#endif

[Setup]
AppId={{7D1F5B2E-9C4A-4E7B-9F3D-2A6C8E1B4D07}
AppName=Labelme
AppVersion={#AppVersion}
AppVerName=Labelme {#AppVersion}
AppPublisher=Labelme
AppPublisherURL=https://labelme.io
AppSupportURL=https://github.com/wkentaro/labelme/issues
AppUpdatesURL=https://github.com/wkentaro/labelme/releases
DefaultDirName={autopf}\Labelme
DefaultGroupName=Labelme
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir={#DistPath}
OutputBaseFilename=labelme-{#AppVersion}-windows-{#ArchSuffix}-setup
SetupIconFile=..\labelme\icons\icon.ico
UninstallDisplayIcon={app}\labelme.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Install per-user by default so no admin prompt is needed, while still letting
; an admin choose a machine-wide install from the dialog.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistPath}\labelme\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Labelme"; Filename: "{app}\labelme.exe"
Name: "{autodesktop}\Labelme"; Filename: "{app}\labelme.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\labelme.exe"; Description: "{cm:LaunchProgram,Labelme}"; Flags: nowait postinstall skipifsilent
