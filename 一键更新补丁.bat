@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "PATCH_RUNTIME=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\patch_runtime"
set "PATCH_APP=%PATCH_RUNTIME%\app"
set "STARTUP=%PATCH_RUNTIME%\creolight_startup.py"
set "LAUNCHER=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\start_patched.bat"
set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"
set "RAW=https://raw.githubusercontent.com/lodgefeng/EES/cursor/fix-python-venv-launch-e627/feature/ai_experiment_judgement/app"

echo ================================================
echo Creolight patch update v3 (run_patched_app.py)
echo ================================================
echo.

if not exist "%PATCH_APP%" mkdir "%PATCH_APP%" >nul 2>&1

set "FAILED=0"
call :dl creolight_startup.py "%STARTUP%"
call :dl patch_sync.py "%PATCH_APP%\patch_sync.py"
call :dl launcher_entry.py "%PATCH_APP%\launcher_entry.py"
call :dl home_menu_patch.py "%PATCH_APP%\home_menu_patch.py"
call :dl ar_imaging_adjustment.py "%PATCH_APP%\ar_imaging_adjustment.py"
call :dl ai_experiment_llm_judgement.py "%PATCH_APP%\ai_experiment_llm_judgement.py"
call :dl experiment_shared.py "%PATCH_APP%\experiment_shared.py"
call :dl ollama_vision_client.py "%PATCH_APP%\ollama_vision_client.py"
call :dl jbd4020_cast_support.py "%PATCH_APP%\jbd4020_cast_support.py"
call :dl ai_experiment_judgement.py "%PATCH_APP%\ai_experiment_judgement.py"
call :dl run_patched_app.py "%PATCH_RUNTIME%\run_patched_app.py"

echo.
if not "%FAILED%"=="0" (
  echo ERROR: download failed. Check internet.
  pause
  exit /b 1
)

if not exist "%STARTUP%" (
  echo ERROR: creolight_startup.py still missing.
  pause
  exit /b 1
)

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
  echo cd /d "%%APP_DIR%%"
  echo "%%APP_DIR%%\python_venv\Scripts\python.exe" -m app.main ^>^> "%%LOG_DIR%%\launcher.log" 2^>^&1
  echo if errorlevel 1 pause
) > "%LAUNCHER%"

echo SUCCESS.
echo.
echo Required file OK:
echo   %STARTUP%
echo.
echo Start app with:
echo   %LAUNCHER%
echo.
pause
exit /b 0

:dl
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%RAW%/%~1' -OutFile '%~2' -UseBasicParsing; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo   [FAIL] %~1
  set "FAILED=1"
) else (
  echo   [OK] %~2
)
exit /b 0
