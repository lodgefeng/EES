@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
set "TOOL=%ROOT_DIR%tools\windows\build_ar_camera_ollama_installer.bat"

if not exist "%TOOL%" (
  echo ERROR: Missing build tool:
  echo   "%TOOL%"
  echo.
  echo Your project folder does not contain tools\windows yet.
  echo Copy the whole tools\windows folder into this project, or update this
  echo project from the branch that contains the Windows install helpers.
  echo.
  echo Expected folder:
  echo   "%ROOT_DIR%tools\windows"
  echo.
  pause
  exit /b 1
)

call "%TOOL%" %*
exit /b %ERRORLEVEL%
