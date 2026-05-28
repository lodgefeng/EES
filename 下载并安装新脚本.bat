@echo off
setlocal EnableExtensions

set "TARGET_DIR=%~1"
if not defined TARGET_DIR set "TARGET_DIR=C:\Users\lodge\AR_Camera_Ollama"
for %%I in ("%TARGET_DIR%.") do set "TARGET_DIR=%%~fI"

set "ZIP_URL=https://github.com/lodgefeng/EES/archive/refs/heads/cursor/fix-python-venv-launch-e627.zip"
set "WORK_DIR=%TEMP%\ar_camera_ollama_helpers"
set "ZIP_PATH=%WORK_DIR%\helpers.zip"
set "EXTRACT_DIR=%WORK_DIR%\extract"
set "TARGET_TOOLS=%TARGET_DIR%\tools\windows"

echo Downloading AR_Camera_Ollama helper scripts...
echo Target:
echo   "%TARGET_DIR%"
echo.

if not exist "%TARGET_DIR%\" (
  echo ERROR: Target project folder does not exist:
  echo   "%TARGET_DIR%"
  echo.
  echo Usage:
  echo   download-and-install-helpers.bat "C:\Users\lodge\AR_Camera_Ollama"
  echo.
  pause
  exit /b 1
)

if exist "%WORK_DIR%" rmdir /S /Q "%WORK_DIR%" >nul 2>&1
mkdir "%WORK_DIR%" >nul 2>&1
mkdir "%EXTRACT_DIR%" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_PATH%'"
if errorlevel 1 (
  echo ERROR: Failed to download helper zip.
  echo URL:
  echo   %ZIP_URL%
  echo.
  echo Check network access to GitHub and try again.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%EXTRACT_DIR%' -Force"
if errorlevel 1 (
  echo ERROR: Failed to extract helper zip.
  pause
  exit /b 1
)

set "HELPER_ROOT="
for /D %%D in ("%EXTRACT_DIR%\*") do (
  if exist "%%~fD\tools\windows\" set "HELPER_ROOT=%%~fD"
)

if not defined HELPER_ROOT (
  echo ERROR: Could not find extracted helper root.
  echo Expected folder:
  echo   tools\windows
  echo.
  pause
  exit /b 1
)

if not exist "%TARGET_DIR%\tools" mkdir "%TARGET_DIR%\tools" >nul 2>&1
if not exist "%TARGET_TOOLS%" mkdir "%TARGET_TOOLS%" >nul 2>&1

for %%F in ("%HELPER_ROOT%\*.bat") do (
  copy /Y "%%~fF" "%TARGET_DIR%\%%~nxF" >nul
  if errorlevel 1 (
    echo ERROR: Could not copy root file: %%~nxF
    pause
    exit /b 1
  )
  echo Copied root file: %%~nxF
)

for %%F in ("%HELPER_ROOT%\tools\windows\*") do (
  copy /Y "%%~fF" "%TARGET_TOOLS%\%%~nxF" >nul
  if errorlevel 1 (
    echo ERROR: Could not copy tool file: %%~nxF
    pause
    exit /b 1
  )
  echo Copied tool file: %%~nxF
)

call :copy_ai_feature "%HELPER_ROOT%" "%TARGET_DIR%"
if errorlevel 1 exit /b 1

if exist "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix\" (
  call :copy_ai_feature "%HELPER_ROOT%" "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix"
  if errorlevel 1 exit /b 1
)

echo.
echo Helper scripts installed successfully.
echo.
echo Next run:
echo   the no-python-check package script in the project root
echo.
pause
exit /b 0

:copy_ai_feature
set "HELPER_SOURCE=%~1"
set "FEATURE_TARGET=%~2"
set "FEATURE_SOURCE=%HELPER_SOURCE%\feature\ai_experiment_judgement\app\ai_experiment_judgement.py"
if not exist "%FEATURE_SOURCE%" exit /b 0
if not exist "%FEATURE_TARGET%\app" mkdir "%FEATURE_TARGET%\app" >nul 2>&1
copy /Y "%FEATURE_SOURCE%" "%FEATURE_TARGET%\app\ai_experiment_judgement.py" >nul
if errorlevel 1 (
  echo ERROR: Could not copy AI experiment feature to:
  echo   "%FEATURE_TARGET%\app"
  pause
  exit /b 1
)
if exist "%HELPER_SOURCE%\tools\windows\launch_ai_experiment_judgement.bat" (
  copy /Y "%HELPER_SOURCE%\tools\windows\launch_ai_experiment_judgement.bat" "%FEATURE_TARGET%\launch_ai_experiment_judgement.bat" >nul
)
echo Copied AI experiment feature to: "%FEATURE_TARGET%"
exit /b 0
