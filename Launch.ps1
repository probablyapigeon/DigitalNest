$ErrorActionPreference = 'Stop'
$habitatUrl = 'http://127.0.0.1:8877'
$habitatHealthy = $false
try {
    $health = Invoke-RestMethod "$habitatUrl/api/health" -TimeoutSec 2
    $habitatHealthy = $health.game -eq 'little-flock'
} catch { }
if (-not $habitatHealthy) {
    $pythonCommand = (Get-Command python -ErrorAction Stop).Source
    $logDirectory = Join-Path $env:LOCALAPPDATA 'LittleFlock'
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $serverPath = Join-Path $PSScriptRoot 'server.py'
    $serverArguments = '-u "' + $serverPath + '"'
    $process = Start-Process -FilePath $pythonCommand -ArgumentList $serverArguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'server.log') -RedirectStandardError (Join-Path $logDirectory 'server-errors.log') -PassThru
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 300
        try {
            $health = Invoke-RestMethod "$habitatUrl/api/health" -TimeoutSec 1
            if ($health.game -eq 'little-flock') { $habitatHealthy = $true; break }
        } catch { }
        if ($process.HasExited) { break }
    }
    if (-not $habitatHealthy) { throw "Little Flock could not start. See $logDirectory\server-errors.log" }
}
Start-Process $habitatUrl
