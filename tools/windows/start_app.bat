@echo off
setlocal EnableExtensions

set "APP_DIR=%~dp0"
for %%I in ("%APP_DIR%.") do set "APP_DIR=%%~fI"

if exist "%APP_DIR%launch_ar_camera_ollama.bat" (
  call "%APP_DIR%launch_ar_camera_ollama.bat" %*
  exit /b %ERRORLEVEL%
)

echo ERROR: Missing launcher script:
echo   "%APP_DIR%launch_ar_camera_ollama.bat"
echo.
echo Run the home-menu fix script in this folder first.
pause
exit /b 1
