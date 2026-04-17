@echo off
cd /d "%~dp0"
python search_and_replace.py
if errorlevel 1 (
    echo.
    echo Fout bij opstarten. Zorg dat Python is geïnstalleerd.
    pause
)
