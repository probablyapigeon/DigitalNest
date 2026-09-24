# Apply the tested source update to this computer's existing Little Flock install.
# Run explicitly from Apply Local Update.cmd. Saves and replaced files are backed up.
$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$liveRoot = Join-Path $env:USERPROFILE 'source/little-flock'
$saveRoot = Join-Path $env:LOCALAPPDATA 'LittleFlock'
$serverPath = Join-Path $liveRoot 'server.py'
$backupRoot = Join-Path (Split-Path $liveRoot) ('little-flock-before-evolving-worlds-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$files = @('game.py','server.py','conversation.py','lonk_life.py','habitat_life.py',
    'world_building.py','flock_society.py','speech_memory.py','language_archive.py',
    'heart.py','world_identity.py','ambient_dialogue.py','web/app.js','web/life.js',
    'web/life.css','web/worlds.js','web/space-art.js')
if (-not (Test-Path -LiteralPath $serverPath)) { throw "Existing installation not found: $liveRoot" }
foreach ($relative in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $relative))) { throw "Missing source: $relative" }
}
$pythonExe = (Get-Command python -ErrorAction Stop).Source
$listener = Get-NetTCPConnection -LocalPort 8877 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $running = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    $normalized = $running.CommandLine.Replace('/', '\')
    if (-not $normalized.Contains($serverPath.Replace('/', '\'))) {
        throw 'Port 8877 belongs to another process. No files were changed.'
    }
}
New-Item -ItemType Directory -Path (Join-Path $backupRoot 'web'), (Join-Path $backupRoot 'save') -Force | Out-Null
foreach ($relative in $files) {
    $old = Join-Path $liveRoot $relative
    if (Test-Path -LiteralPath $old) { Copy-Item -LiteralPath $old -Destination (Join-Path $backupRoot $relative) }
}
if ($listener) { Stop-Process -Id $running.ProcessId }
$newServer = $null
try {
    Get-ChildItem -LiteralPath $saveRoot -File | Where-Object {
        $_.Name -like 'save*.json' -or $_.Name -like '*.sqlite3'
    } | Copy-Item -Destination (Join-Path $backupRoot 'save')
    foreach ($relative in $files) {
        Copy-Item -LiteralPath (Join-Path $sourceRoot $relative) -Destination (Join-Path $liveRoot $relative) -Force
    }
    $newServer = Start-Process -FilePath $pythonExe -ArgumentList ('-u "' + $serverPath + '"') -WorkingDirectory $liveRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $saveRoot 'server.log') -RedirectStandardError (Join-Path $saveRoot 'server-errors.log') -PassThru
    $healthy = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8877/api/health' -TimeoutSec 2
            if ($health.version -eq 'evolving-worlds-9') { $healthy = $true; break }
        } catch { }
        if ($newServer.HasExited) { break }
    }
    if (-not $healthy) { throw 'Updated server did not start successfully. Check server-errors.log.' }
    Write-Host "Update ready. Backup: $backupRoot"
    Start-Process 'http://127.0.0.1:8877'
} catch {
    $failure = $_
    if ($newServer -and -not $newServer.HasExited) { $newServer.Kill(); $newServer.WaitForExit() }
    foreach ($relative in $files) {
        $old = Join-Path $backupRoot $relative
        if (Test-Path -LiteralPath $old) { Copy-Item -LiteralPath $old -Destination (Join-Path $liveRoot $relative) -Force }
    }
    Get-ChildItem -LiteralPath (Join-Path $backupRoot 'save') -File | Copy-Item -Destination $saveRoot -Force
    Write-Host "Previous files restored. Backup: $backupRoot"
    Write-Host 'Use Start Little Flock.cmd in the little-flock folder to restart the previous version.'
    throw $failure
}
