$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.build-venv\Scripts\python.exe')) {
    python -m venv .build-venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create build environment.' }
}
$buildPython = Join-Path $PSScriptRoot '.build-venv\Scripts\python.exe'
& $buildPython -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install packaging tools.' }
& $buildPython -m PyInstaller --noconfirm DigitalNest.spec
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
New-Item -ItemType Directory -Force release | Out-Null
$report = Join-Path $PSScriptRoot 'release\self-test.json'
$check = Start-Process -FilePath (Join-Path $PSScriptRoot 'dist\DigitalNest\DigitalNest.exe') -ArgumentList ('--self-test "' + $report + '"') -WindowStyle Hidden -Wait -PassThru
if ($check.ExitCode -ne 0 -or -not (Get-Content $report -Raw | ConvertFrom-Json).ok) { throw "Packaged self-test failed. See $report" }
Copy-Item README.md dist\DigitalNest\README.md -Force
New-Item -ItemType Directory -Force dist\DigitalNest\notices | Out-Null
& $buildPython -c "import sys,shutil,importlib.metadata; from pathlib import Path; out=Path('dist/DigitalNest/notices'); shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',out/'Python.txt'); d=importlib.metadata.distribution('pyinstaller'); p=next(p for p in d.files if p.name=='COPYING.txt'); shutil.copy2(d.locate_file(p),out/'PyInstaller.txt')"
if ($LASTEXITCODE -ne 0) { throw 'Could not collect bundled runtime notices.' }
Copy-Item vendor\PROVENANCE.md dist\DigitalNest\notices\LUMINA-provenance.md -Force
Copy-Item vendor\lonkworld\PROVENANCE.md dist\DigitalNest\notices\LonkWorld-provenance.md -Force
Compress-Archive -Path dist\DigitalNest -DestinationPath release\DigitalNest-Windows-x64.zip -Force
Get-FileHash release\DigitalNest-Windows-x64.zip -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  DigitalNest-Windows-x64.zip" } | Set-Content release\SHA256SUMS.txt
Write-Output 'Ready: release\DigitalNest-Windows-x64.zip'
