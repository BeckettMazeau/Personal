# This script restores the default Windows Explorer association for .zip files
# and removes the KiCad Importer from being the default handler.

$zipKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.zip\UserChoice"
$progIdKey = "Registry::HKEY_CLASSES_ROOT\KiCadImporter.Zip"
$openWithKey = "Registry::HKEY_CLASSES_ROOT\.zip\OpenWithProgids"

Write-Host "Restoring .zip file associations..." -ForegroundColor Cyan

# 1. Remove the UserChoice if it was set to KiCadImporter
if (Test-Path $zipKey) {
    $choice = (Get-ItemProperty $zipKey).ProgId
    if ($choice -eq "KiCadImporter.Zip") {
        Write-Host "Removing UserChoice override..."
        Remove-Item $zipKey -Force
    }
}

# 2. Remove the custom ProgID
if (Test-Path $progIdKey) {
    Write-Host "Removing KiCadImporter.Zip ProgID..."
    Remove-Item $progIdKey -Recurse -Force
}

# 3. Remove from OpenWithProgids
if (Test-Path $openWithKey) {
    $props = Get-ItemProperty -Path $openWithKey
    if ($props.PSObject.Properties.Name -contains "KiCadImporter.Zip") {
        Write-Host "Removing from OpenWithProgids..."
        Remove-ItemProperty -Path $openWithKey -Name "KiCadImporter.Zip" -Force
    }
}

# 4. Try to reset to CompressedFolder if no other default exists
$zipDefaultPath = "Registry::HKEY_CLASSES_ROOT\.zip"
if (Test-Path $zipDefaultPath) {
    $defaultZip = (Get-ItemProperty $zipDefaultPath)."(default)"
    if ($defaultZip -eq "KiCadImporter.Zip" -or [string]::IsNullOrEmpty($defaultZip)) {
        Write-Host "Resetting .zip default to CompressedFolder (Windows Explorer)..."
        Set-ItemProperty -Path $zipDefaultPath -Name "(default)" -Value "CompressedFolder"
    }
}

# Refresh the shell
Write-Host "Refreshing shell..."
$code = '[DllImport("shell32.dll")] public static extern void SHChangeNotify(uint wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);'
$type = Add-Type -MemberDefinition $code -Name "Shell32" -Namespace "Win32" -PassThru
$type::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero) # SHCNE_ASSOCCHANGED

Write-Host "Done! Windows Explorer should now be the default for .zip files." -ForegroundColor Green
Write-Host "You may need to restart Explorer or log out for all changes to take effect."
