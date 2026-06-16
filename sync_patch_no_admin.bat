@echo off
setlocal EnableExtensions

set "PATCH_APP=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\patch_runtime\app"
set "PATCH_BRANCH=cursor/fix-python-venv-launch-e627"
set "PATCH_RAW=https://raw.githubusercontent.com/lodgefeng/EES/%PATCH_BRANCH%/feature/ai_experiment_judgement/app"

echo ========================================
echo Sync Creolight menu patch (no admin)
echo ========================================
echo Target:
echo   "%PATCH_APP%"
echo.

if not exist "%PATCH_APP%" mkdir "%PATCH_APP%" >nul 2>&1

set "FAILED=0"
for %%F in (patch_sync.py launcher_entry.py home_menu_patch.py ar_imaging_adjustment.py ai_experiment_llm_judgement.py experiment_shared.py ollama_vision_client.py jbd4020_cast_support.py ai_experiment_judgement.py) do (
  call :download %%F
)

echo.
if not "%FAILED%"=="0" (
  echo Some files failed to download. Check your internet connection.
) else (
  call :download_runner
  echo SUCCESS. Patch files saved to LOCALAPPDATA.
  call :write_user_launcher
  echo.
  echo You can start the app with:
  echo   "%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\start_patched.bat"
  echo.
  echo Or restart from the normal Creolight shortcut after one admin fix of start_app.bat.
)
echo.
pause
exit /b 0

:download_runner
set "PATCH_RUNTIME=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\patch_runtime"
if not exist "%PATCH_RUNTIME%" mkdir "%PATCH_RUNTIME%" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$u='%PATCH_RAW%/run_patched_app.py';" ^
  "$o='%PATCH_RUNTIME%\run_patched_app.py';" ^
  "Invoke-WebRequest -Uri $u -OutFile $o -UseBasicParsing"
if errorlevel 1 (
  echo   [FAIL] run_patched_app.py
  set "FAILED=1"
) else (
  echo   [OK] %PATCH_RUNTIME%\run_patched_app.py
)
exit /b 0

:write_user_launcher
set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"
set "LAUNCHER=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\start_patched.bat"
set "PATCH_RUNTIME=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\patch_runtime"
set "RUNNER=%PATCH_RUNTIME%\run_patched_app.py"
(
  echo @echo off
  echo setlocal EnableExtensions
  echo set "APP_DIR=%INSTALL_DIR%"
  echo set "PATCH_RUNTIME=%PATCH_RUNTIME%"
  echo set "CREOLIGHT_APP_DIR=%%APP_DIR%%"
  echo set "CREOLIGHT_PATCH_RUNTIME=%%PATCH_RUNTIME%%"
  echo set "LOG_DIR=%%LOCALAPPDATA%%\Creolight\AR_Camera_Ollama"
  echo if not exist "%%LOG_DIR%%" mkdir "%%LOG_DIR%%" ^>nul 2^>^&1
  echo if not exist "%%PATCH_RUNTIME%%\app" mkdir "%%PATCH_RUNTIME%%\app" ^>nul 2^>^&1
  echo if not exist "%RUNNER%" (
  echo   echo ERROR: Missing %RUNNER%
  echo   echo Run sync_patch_no_admin.bat first.
  echo   pause
  echo   exit /b 1
  echo ^)
  echo "%%APP_DIR%%\python_venv\Scripts\python.exe" "%RUNNER%" ^>^> "%%LOG_DIR%%\launcher.log" 2^>^&1
  echo if errorlevel 1 pause
) > "%LAUNCHER%"
echo   [OK] wrote %LAUNCHER%
exit /b 0

:download
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$u='%PATCH_RAW%/%~1';" ^
  "$o='%PATCH_APP%\%~1';" ^
  "Invoke-WebRequest -Uri $u -OutFile $o -UseBasicParsing"
if errorlevel 1 (
  echo   [FAIL] %~1
  set "FAILED=1"
) else (
  echo   [OK] %~1
)
exit /b 0
