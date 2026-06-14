$ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path

$ShortcutName = "Boxing Journey 2026.lnk"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath $ShortcutName

$BatPath = Join-Path $ProjectPath "run_boxing_app.bat"
$IconPath = Join-Path $ProjectPath "assets\logos\boxing_logo_shortcut_v2.ico"

$CmdPath = "$env:SystemRoot\System32\cmd.exe"

if (-not (Test-Path $BatPath)) {
    Write-Host "ERROR: run_boxing_app.bat was not found." -ForegroundColor Red
    Write-Host $BatPath
    Pause
    exit
}

if (-not (Test-Path $CmdPath)) {
    Write-Host "ERROR: cmd.exe was not found." -ForegroundColor Red
    Write-Host $CmdPath
    Pause
    exit
}

if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
}

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)

$Shortcut.TargetPath = $CmdPath
$Shortcut.Arguments = "/k `"$BatPath`""
$Shortcut.WorkingDirectory = $ProjectPath
$Shortcut.Description = "Launch Boxing Journey 2026"

if (Test-Path $IconPath) {
    $Shortcut.IconLocation = "$IconPath,0"
}
else {
    Write-Host "WARNING: Icon file not found:" -ForegroundColor Yellow
    Write-Host $IconPath
    Write-Host "Shortcut will be created without custom icon."
}

$Shortcut.Save()

Write-Host ""
Write-Host "Desktop shortcut created:" -ForegroundColor Green
Write-Host $ShortcutPath
Write-Host ""
Write-Host "Right-click desktop and choose Refresh."
Pause