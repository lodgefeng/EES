@echo off
setlocal EnableExtensions

set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"
set "ZIP_URL=https://github.com/lodgefeng/EES/archive/refs/heads/cursor/fix-python-venv-launch-e627.zip"
set "WORK_DIR=%TEMP%\creolight_button05_fix"
set "ZIP_PATH=%WORK_DIR%\helpers.zip"
set "EXTRACT_DIR=%WORK_DIR%\extract"
set "VENV_PY=%INSTALL_DIR%\python_venv\Scripts\python.exe"
set "REPAIR_PY="

net session >nul 2>&1
if errorlevel 1 (
  echo Need administrator permission to write:
  echo   "%INSTALL_DIR%"
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

echo ========================================
echo Repair broken main.py from button-05 patch
echo ========================================
echo Target:
echo   "%INSTALL_DIR%"
echo.

if not exist "%INSTALL_DIR%\app\main.py" (
  echo ERROR: Missing app\main.py
  pause
  exit /b 1
)

echo [1/2] Downloading repair tool from GitHub...
if exist "%WORK_DIR%" rmdir /S /Q "%WORK_DIR%" >nul 2>&1
mkdir "%WORK_DIR%" >nul 2>&1
mkdir "%EXTRACT_DIR%" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_PATH%'"
if errorlevel 1 (
  echo ERROR: Download failed.
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
  if exist "%%~fD\tools\windows\repair_main_py_menu_patch.py" set "HELPER_ROOT=%%~fD"
)

if not defined HELPER_ROOT (
  echo ERROR: Could not find repair tool in downloaded zip.
  pause
  exit /b 1
)

set "REPAIR_PY=%HELPER_ROOT%\tools\windows\repair_main_py_menu_patch.py"

echo [2/2] Repairing app\main.py ...
set "REPAIRED=0"

if exist "%VENV_PY%" (
  echo Using: "%VENV_PY%"
  "%VENV_PY%" "%REPAIR_PY%" "%INSTALL_DIR%"
  if not errorlevel 1 set "REPAIRED=1"
)

if not "%REPAIRED%"=="1" (
  echo venv python failed, trying system python...
  for %%P in (python python3) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
      %%P "%REPAIR_PY%" "%INSTALL_DIR%"
      if not errorlevel 1 set "REPAIRED=1" & goto repaired
    )
  )
)

:repaired
if not "%REPAIRED%"=="1" (
  echo.
  echo ERROR: Could not run repair tool.
  echo Check that this file exists:
  echo   "%VENV_PY%"
  pause
  exit /b 1
)

echo.
echo Repair finished successfully.
echo Button 05 still works via launcher_entry runtime patch.
echo.
echo Next:
echo   1. Close the app completely
echo   2. Open again from desktop shortcut
echo.
pause
exit /b 0
