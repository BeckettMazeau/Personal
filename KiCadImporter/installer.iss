[Setup]
AppName=KiCad Import Tool
AppVersion=1.0.0
DefaultDirName={pf}\KiCad Import Tool
DefaultGroupName=KiCad Import Tool
OutputBaseFilename=KiCadImporter_v1.0_Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ChangesAssociations=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\KiCadImporter_v1.0.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\KiCad Import Tool"; Filename: "{app}\KiCadImporter_v1.0.exe"
Name: "{commondesktop}\KiCad Import Tool"; Filename: "{app}\KiCadImporter_v1.0.exe"; Tasks: desktopicon

[Registry]
; Associate the application with .zip files if the user chooses
Root: HKCR; Subkey: ".zip\OpenWithProgids"; ValueType: string; ValueName: "KiCadImporter.Zip"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCR; Subkey: "KiCadImporter.Zip"; ValueType: string; ValueData: "Zip Archive for KiCad Importer"; Flags: uninsdeletekey
Root: HKCR; Subkey: "KiCadImporter.Zip\DefaultIcon"; ValueType: string; ValueData: "{app}\KiCadImporter_v1.0.exe,0"
Root: HKCR; Subkey: "KiCadImporter.Zip\shell\open\command"; ValueType: string; ValueData: """{app}\KiCadImporter_v1.0.exe"" ""%1"""

[Run]
Filename: "{app}\KiCadImporter_v1.0.exe"; Description: "{cm:LaunchProgram,KiCad Import Tool}"; Flags: nowait postinstall skipifsilent
