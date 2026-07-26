@echo off
title Transcriptor de Bandurria a MIDI
cd /d "%~dp0"
echo ========================================================
echo   Iniciando Transcriptor de Bandurria a MIDI (GUI)
echo ========================================================
.\.venv\Scripts\python.exe gui.py
pause
