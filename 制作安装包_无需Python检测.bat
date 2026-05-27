@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
set "TOOL=%ROOT_DIR%build_ar_camera_ollama_installer.bat"

if not exist "%TOOL%" (
  echo ERROR: Missing installer build entrypoint:
  echo   "%TOOL%"
  echo.
  echo This is the no-portable-venv packaging entrypoint.
  echo It does not use Anaconda or create python_venv during packaging.
  echo.
  echo Copy these files into the project root first:
  echo   build_ar_camera_ollama_installer.bat
  echo   tools\windows
  echo.
  pause
  exit /b 1
)

call "%TOOL%" %*
exit /b %ERRORLEVEL%
