; Inno-Setup-Skript für gmlConverter
; Build: ISCC.exe /DAppVersion=1.3.0 installer.iss
; Erwartet den PyInstaller-onedir-Output unter dist\gmlConverter\

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{8F6A2C4D-6F1B-4E3B-9C7D-2A5E8B1D4F90}
AppName=gmlConverter
AppVersion={#AppVersion}
AppPublisher=Krekeler Architekten Generalplaner GmbH
AppPublisherURL=https://krekeler-architekten.de/
DefaultDirName={autopf}\gmlConverter
DefaultGroupName=gmlConverter
DisableProgramGroupPage=yes
; Installation ohne Admin-Rechte ins Benutzerprofil
PrivilegesRequired=lowest
OutputDir=installer_out
OutputBaseFilename=gmlConverter-Setup
SetupIconFile=citygml_converter\__files__\kgp.ico
UninstallDisplayIcon={app}\gmlConverter.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\gmlConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\gmlConverter"; Filename: "{app}\gmlConverter.exe"
Name: "{autodesktop}\gmlConverter"; Filename: "{app}\gmlConverter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\gmlConverter.exe"; Description: "{cm:LaunchProgram,gmlConverter}"; Flags: nowait postinstall skipifsilent
