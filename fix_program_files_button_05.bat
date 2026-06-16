@echo off
setlocal EnableExtensions

set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"
set "ZIP_URL=https://github.com/lodgefeng/EES/archive/refs/heads/cursor/fix-python-venv-launch-e627.zip"
set "WORK_DIR=%TEMP%\creolight_button05_fix"
set "ZIP_PATH=%WORK_DIR%\helpers.zip"
set "EXTRACT_DIR=%WORK_DIR%\extract"

net session >nul 2>&1
if errorlevel 1 (
  echo Need administrator permission to write:
  echo   "%INSTALL_DIR%"
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

echo ========================================
echo Fix home button 05 for Program Files install
echo ========================================
echo Target:
echo   "%INSTALL_DIR%"
echo.

if not exist "%INSTALL_DIR%\app\main.py" (
  echo ERROR: Install folder not found or missing app\main.py:
  echo   "%INSTALL_DIR%"
  pause
  exit /b 1
)

echo [1/4] Downloading latest helper files from GitHub...
if exist "%WORK_DIR%" rmdir /S /Q "%WORK_DIR%" >nul 2>&1
mkdir "%WORK_DIR%" >nul 2>&1
mkdir "%EXTRACT_DIR%" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_PATH%'"
if errorlevel 1 (
  echo ERROR: Download failed.
  echo URL: %ZIP_URL%
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%EXTRACT_DIR%' -Force"
if errorlevel 1 (
  echo ERROR: Could not extract zip.
  pause
  exit /b 1
)

set "HELPER_ROOT="
for /D %%D in ("%EXTRACT_DIR%\*") do (
  if exist "%%~fD\feature\ai_experiment_judgement\app\home_menu_patch.py" set "HELPER_ROOT=%%~fD"
)

if not defined HELPER_ROOT (
  echo ERROR: Could not find helper files in downloaded zip.
  pause
  exit /b 1
)

echo [2/4] Copying patch files into Program Files...
if not exist "%INSTALL_DIR%\app" mkdir "%INSTALL_DIR%\app" >nul 2>&1

copy /Y "%HELPER_ROOT%\feature\ai_experiment_judgement\app\ai_experiment_judgement.py" "%INSTALL_DIR%\app\ai_experiment_judgement.py" >nul
if errorlevel 1 goto copy_failed
copy /Y "%HELPER_ROOT%\feature\ai_experiment_judgement\app\home_menu_patch.py" "%INSTALL_DIR%\app\home_menu_patch.py" >nul
if errorlevel 1 goto copy_failed
copy /Y "%HELPER_ROOT%\feature\ai_experiment_judgement\app\launcher_entry.py" "%INSTALL_DIR%\app\launcher_entry.py" >nul
if errorlevel 1 goto copy_failed
copy /Y "%HELPER_ROOT%\tools\windows\start_app.bat" "%INSTALL_DIR%\start_app.bat" >nul
if errorlevel 1 goto copy_failed
copy /Y "%HELPER_ROOT%\tools\windows\launch_ar_camera_ollama.bat" "%INSTALL_DIR%\launch_ar_camera_ollama.bat" >nul
if errorlevel 1 goto copy_failed

echo [3/4] Patching app\main.py if possible...
for %%P in ("py -3.11" "py -3.10" "py -3.9" "py -3" "python" "python3") do (
  if exist "%HELPER_ROOT%\tools\windows\patch_main_menu_button_05.py" (
    %%~P "%HELPER_ROOT%\tools\windows\patch_main_menu_button_05.py" "%INSTALL_DIR%" >nul 2>&1 && goto patched_main
  )
)
:patched_main

echo [4/4] Verifying files...
set "MISSING=0"
call :check_file "%INSTALL_DIR%\app\home_menu_patch.py"
call :check_file "%INSTALL_DIR%\app\launcher_entry.py"
call :check_file "%INSTALL_DIR%\app\ai_experiment_judgement.py"
call :check_file "%INSTALL_DIR%\start_app.bat"
call :check_file "%INSTALL_DIR%\launch_ar_camera_ollama.bat"

if not "%MISSING%"=="0" (
  echo.
  echo ERROR: Some files are still missing. Copy may have failed.
  pause
  exit /b 1
)

echo.
echo SUCCESS. Required files are now in:
echo   "%INSTALL_DIR%\app"
echo.
echo Next steps:
echo   1. Close AR Camera Ollama completely
echo   2. Open again from desktop shortcut
echo   3. You should see button 05 on the home page
echo.
echo After restart, logs should appear here:
echo   %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\launcher.log
echo   %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\home_menu_patch.log
echo.
pause
exit /b 0

:check_file
if exist "%~1" (
  echo   [OK] %~1
) else (
  echo   [MISSING] %~1
  set "MISSING=1"
)
exit /b 0

:copy_failed
echo.
echo ERROR: Could not copy files into Program Files.
echo Make sure you run this script as administrator.
pause
exit /b 1
