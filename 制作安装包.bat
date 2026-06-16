@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
set "TOOL=%ROOT_DIR%build_ar_camera_ollama_installer.bat"

if not exist "%TOOL%" (
  echo ERROR: Missing installer build entrypoint:
  echo   "%TOOL%"
  echo.
  echo This script should be placed in the AR_Camera_Ollama project root
  echo together with build_ar_camera_ollama_installer.bat and tools\windows.
  echo.
  pause
  exit /b 1
)

call "%TOOL%" %*
exit /b %ERRORLEVEL%
