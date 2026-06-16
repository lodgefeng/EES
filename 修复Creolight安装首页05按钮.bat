@echo off
setlocal EnableExtensions

set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"

echo Fixing home menu button 05 for Creolight install:
echo   "%INSTALL_DIR%"
echo.
echo If copy fails, right-click this file and choose Run as administrator.
echo.

call "%~dp0修复首页05按钮.bat" "%INSTALL_DIR%"
exit /b %ERRORLEVEL%
