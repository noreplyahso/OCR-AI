#ifndef AppName
  #define AppName "DRB-OCR-AI"
#endif

#ifndef AppExeName
  #define AppExeName "DRB-OCR-AI.exe"
#endif

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#ifndef SourceDir
  #define SourceDir "..\dist\DRB-OCR-AI"
#endif

#ifndef RepoRoot
  #define RepoRoot ".."
#endif

#ifndef OutputDir
  #define OutputDir "..\dist\installer"
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename "DRB-OCR-AI-setup"
#endif

[Setup]
AppId={{4D45C7AF-6E55-4C35-8263-3D93AD01CA0D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=DRB
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile={#RepoRoot}\Icon\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
SetupLogging=yes
InfoAfterFile={#RepoRoot}\installer\INSTALL_REQUIREMENTS.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
