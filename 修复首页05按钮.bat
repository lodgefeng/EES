@echo off
setlocal EnableExtensions

set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR=%%~fI"
set "TARGET_DIR=%~1"
if not defined TARGET_DIR set "TARGET_DIR=%~dp0"
for %%I in ("%TARGET_DIR%.") do set "TARGET_DIR=%%~fI"

echo Fixing home menu button 05 for:
echo   "%TARGET_DIR%"
echo.

call "%SOURCE_DIR%安装AI实验判断功能.bat" "%TARGET_DIR%"
if errorlevel 1 exit /b 1

if exist "%SOURCE_DIR%tools\windows\launch_ar_camera_ollama.bat" (
  copy /Y "%SOURCE_DIR%tools\windows\launch_ar_camera_ollama.bat" "%TARGET_DIR%\launch_ar_camera_ollama.bat" >nul
  if errorlevel 1 (
    echo ERROR: Could not update launch_ar_camera_ollama.bat
    echo Try running this script as administrator.
    pause
    exit /b 1
  )
)

if exist "%SOURCE_DIR%tools\windows\start_app.bat" (
  copy /Y "%SOURCE_DIR%tools\windows\start_app.bat" "%TARGET_DIR%\start_app.bat" >nul
  if errorlevel 1 (
    echo ERROR: Could not update start_app.bat
    echo Try running this script as administrator.
    pause
    exit /b 1
  )
)

if exist "%SOURCE_DIR%tools\windows\patch_main_menu_button_05.py" (
  for %%P in ("py -3.11" "py -3.10" "py -3.9" "py -3" "python" "python3") do (
    if exist "%TARGET_DIR%\app\main.py" (
      %%~P "%SOURCE_DIR%tools\windows\patch_main_menu_button_05.py" "%TARGET_DIR%" && goto patched
    )
  )
)

:patched
echo.
echo Done. Close the app and open it again from the desktop shortcut.
echo You should see:
echo   05 ^| AI实验判断
echo.
pause
exit /b 0
