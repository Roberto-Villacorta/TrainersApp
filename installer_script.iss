; Script de Inno Setup para TrainersApp
; Generado por Antigravity

[Setup]
; Información básica del App
AppId={{C6E2A3B4-D5E6-4F7A-8B9C-0D1E2F3A4B5C}}
AppName=TrainersApp
AppVersion=1.0.0
AppPublisher=Roberto Villacorta
AppPublisherURL=https://github.com/Roberto-Villacorta/TrainersApp
AppSupportURL=https://github.com/Roberto-Villacorta/TrainersApp
AppUpdatesURL=https://github.com/Roberto-Villacorta/TrainersApp
DefaultDirName={autopf}\TrainersApp
DisableProgramGroupPage=yes
; El ejecutable resultante se guardará en la carpeta 'Output'
OutputDir=installer_output
OutputBaseFilename=TrainersApp_Setup
;SetupIconFile=

Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copiar todos los archivos generados por PyInstaller
Source: "dist\TrainersApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTA: Si tienes un icono, añádelo aquí y en SetupIconFile

[Icons]
Name: "{autoprograms}\TrainersApp"; Filename: "{app}\TrainersApp.exe"
Name: "{autodesktop}\TrainersApp"; Filename: "{app}\TrainersApp.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TrainersApp.exe"; Description: "{cm:LaunchProgram,TrainersApp}"; Flags: nowait postinstall skipifsilent
