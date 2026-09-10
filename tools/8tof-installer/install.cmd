@echo off
py -3 "%~dp0install.py" --board horizontal-v3 %*
exit /b %errorlevel%
