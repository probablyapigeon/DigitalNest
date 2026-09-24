@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Apply-Local-Update.ps1"
if errorlevel 1 pause
