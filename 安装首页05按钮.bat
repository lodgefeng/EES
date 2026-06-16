@echo off
setlocal EnableExtensions

set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR=%%~fI"
set "PROJECT_DIR=%~1"
if not defined PROJECT_DIR set "PROJECT_DIR=C:\Users\lodge\AR_Camera_Ollama"
for %%I in ("%PROJECT_DIR%.") do set "PROJECT_DIR=%%~fI"

set "PATCHER=%SOURCE_DIR%tools\windows\patch_main_menu_button_05.py"
set "MAIN_PY=%PROJECT_DIR%\app\main.py"

echo Patching home menu button 05...
echo Project:
echo   "%PROJECT_DIR%"
echo.

if not exist "%MAIN_PY%" (
  echo ERROR: Missing main.py:
  echo   "%MAIN_PY%"
  pause
  exit /b 1
)

if not exist "%PATCHER%" (
  echo ERROR: Missing patcher:
  echo   "%PATCHER%"
  pause
  exit /b 1
)

call "%SOURCE_DIR%安装AI实验判断功能.bat" "%PROJECT_DIR%"
if errorlevel 1 exit /b 1

for %%P in ("py -3.11" "py -3.10" "py -3.9" "py -3" "python" "python3") do (
  %%~P "%PATCHER%" "%PROJECT_DIR%" && goto patched
)

echo ERROR: Could not find Python to run the menu patcher.
pause
exit /b 1

:patched
echo.
echo Home menu patch finished.
echo Restart AR Camera Ollama and check button:
echo   05 button on home page
echo.
pause
exit /b 0
