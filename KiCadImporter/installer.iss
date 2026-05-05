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
; Register the application in the 'Applications' key for 'Open With' support
; This adds it to the "Open With" list without making it the default opener for .zip files.
Root: HKCR; Subkey: "Applications\KiCadImporter_v1.0.exe\shell\open\command"; ValueType: string; ValueData: """{app}\KiCadImporter_v1.0.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\KiCadImporter_v1.0.exe\SupportedTypes"; ValueType: string; ValueName: ".zip"; ValueData: ""; Flags: uninsdeletekey

[Run]
Filename: "{app}\KiCadImporter_v1.0.exe"; Description: "{cm:LaunchProgram,KiCad Import Tool}"; Flags: nowait postinstall skipifsilent
