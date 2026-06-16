@echo off
setlocal EnableExtensions

set "PATCH_RUNTIME=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\patch_runtime"
set "PATCH_APP=%PATCH_RUNTIME%\app"
set "STARTUP=%PATCH_RUNTIME%\creolight_startup.py"
set "PATCH_BRANCH=cursor/fix-python-venv-launch-e627"
set "PATCH_RAW=https://raw.githubusercontent.com/lodgefeng/EES/%PATCH_BRANCH%/feature/ai_experiment_judgement/app"
set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"

echo ========================================
echo Sync Creolight menu patch (no admin)
echo ========================================
echo Target:
echo   "%PATCH_APP%"
echo.

if not exist "%PATCH_APP%" mkdir "%PATCH_APP%" >nul 2>&1
if not exist "%PATCH_RUNTIME%" mkdir "%PATCH_RUNTIME%" >nul 2>&1

set "FAILED=0"
for %%F in (creolight_startup.py patch_sync.py launcher_entry.py home_menu_patch.py ar_imaging_adjustment.py ai_experiment_llm_judgement.py experiment_shared.py ollama_vision_client.py jbd4020_cast_support.py ai_experiment_judgement.py) do (
  call :download_module %%F
)
call :download_runner

echo.
if not "%FAILED%"=="0" (
  echo Some files failed to download. Check your internet connection.
) else (
  echo SUCCESS. Patch files saved to LOCALAPPDATA.
  call :write_user_launcher
  echo.
  echo Start the app with:
  echo   "%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\start_patched.bat"
)
echo.
pause
exit /b 0

:download_module
set "TARGET=%PATCH_APP%\%~1"
if /I "%~1"=="creolight_startup.py" set "TARGET=%STARTUP%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$u='%PATCH_RAW%/%~1';" ^
  "$o='%TARGET%';" ^
  "Invoke-WebRequest -Uri $u -OutFile $o -UseBasicParsing"
if errorlevel 1 (
  echo   [FAIL] %~1
  set "FAILED=1"
) else (
  echo   [OK] %TARGET%
)
exit /b 0

:download_runner
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
set "LAUNCHER=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\start_patched.bat"
(
  echo @echo off
  echo setlocal EnableExtensions
  echo set "APP_DIR=%INSTALL_DIR%"
  echo set "PATCH_RUNTIME=%PATCH_RUNTIME%"
  echo set "CREOLIGHT_APP_DIR=%%APP_DIR%%"
  echo set "CREOLIGHT_PATCH_RUNTIME=%%PATCH_RUNTIME%%"
  echo set "PYTHONSTARTUP=%%PATCH_RUNTIME%%\creolight_startup.py"
  echo set "LOG_DIR=%%LOCALAPPDATA%%\Creolight\AR_Camera_Ollama"
  echo if not exist "%%LOG_DIR%%" mkdir "%%LOG_DIR%%" ^>nul 2^>^&1
  echo if not exist "%%PYTHONSTARTUP%%" (
  echo   echo ERROR: Missing patch startup file:
  echo   echo   %%PYTHONSTARTUP%%
  echo   echo Run sync_patch_no_admin.bat first.
  echo   pause
  echo   exit /b 1
  echo ^)
  echo cd /d "%%APP_DIR%%"
  echo "%%APP_DIR%%\python_venv\Scripts\python.exe" -m app.main ^>^> "%%LOG_DIR%%\launcher.log" 2^>^&1
  echo if errorlevel 1 pause
) > "%LAUNCHER%"
echo   [OK] wrote %LAUNCHER%
exit /b 0
