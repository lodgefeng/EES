@echo off
setlocal EnableExtensions

set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"

net session >nul 2>&1
if errorlevel 1 (
  echo Requesting administrator permission for:
  echo   "%INSTALL_DIR%"
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

echo Fixing home menu button 05 for Creolight install:
echo   "%INSTALL_DIR%"
echo.

call "%~dp0修复首页05按钮.bat" "%INSTALL_DIR%"
exit /b %ERRORLEVEL%
