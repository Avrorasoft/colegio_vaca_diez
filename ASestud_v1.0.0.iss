; ==============================================================================
; Script de Instalación - ASestud
; Desarrollado por: Avrora Soft - Vibola LLC
; ==============================================================================

#define NombreApp "ASestud"
#define VersionApp "1.0.0"
#define EmpresaApp "Avrora Soft - Vibola LLC"
#define EjecutableApp "ASestud.exe"

[Setup]
AppId={{ASestud-AvroraSoft-Vibola}}
AppName={#NombreApp}
AppVersion={#VersionApp}
AppPublisher={#EmpresaApp}
DefaultDirName={autopf}\ASestud
DefaultGroupName={#NombreApp}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=Instalador_ASestud_v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Dirs]
Name: "{app}\instance"; Flags: uninsneveruninstall
Name: "{app}\static\backups"; Flags: uninsneveruninstall
Name: "{app}\static\uploads"; Flags: uninsneveruninstall

[Files]
Source: "dist\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "instance\colegio_vaca_diez.db"; DestDir: "{app}\instance"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#NombreApp}"; Filename: "{app}\{#EjecutableApp}"
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\{#EjecutableApp}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#EjecutableApp}"; Description: "{cm:LaunchProgram,{#StringChange(NombreApp, '&', '&&')}}"; Flags: nowait postinstall skipifsilent