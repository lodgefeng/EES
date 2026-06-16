@echo off
setlocal EnableExtensions

set "APP_DIR=%~dp0"
for %%I in ("%APP_DIR%.") do set "APP_DIR=%%~fI"
set "VENV_PY=%APP_DIR%\python_venv\Scripts\python.exe"
set "REPAIR=%APP_DIR%\repair_python_venv.bat"
set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LOG_FILE=%LOG_DIR%\launcher.log"
set "PATCH_RUNTIME=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\patch_runtime"
set "PATCH_APP=%PATCH_RUNTIME%\app"
set "PATCH_BRANCH=cursor/fix-python-venv-launch-e627"
set "PATCH_RAW=https://raw.githubusercontent.com/lodgefeng/EES/%PATCH_BRANCH%/feature/ai_experiment_judgement/app"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1
if not exist "%PATCH_APP%" mkdir "%PATCH_APP%" >nul 2>&1
call :log "start_app.bat launched."
call :log "App directory: %APP_DIR%"

cd /d "%APP_DIR%" || (
  call :log "ERROR: Could not change to app directory."
  echo ERROR: Could not change to "%APP_DIR%".
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  call :log "python_venv is missing."
  echo python_venv is missing or incomplete.
  echo.
  if exist "%REPAIR%" (
    echo Running repair script first...
    call "%REPAIR%"
  ) else (
    echo Copy repair_python_venv.bat into this folder and run it.
  )
)

if not exist "%VENV_PY%" (
  call :log "ERROR: Virtual environment is still missing."
  echo ERROR: "%VENV_PY%" does not exist.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

call :sync_patch_modules

set "ENTRY="
for %%F in (main.py app.py run.py ar_camera_ollama.py AR_Camera_Ollama.py camera_ollama.py app\main.py app\app.py app\run.py app\ar_camera_ollama.py app\AR_Camera_Ollama.py app\camera_ollama.py src\main.py src\app.py scripts\main.py scripts\run.py) do (
  if not defined ENTRY if exist "%APP_DIR%\%%F" set "ENTRY=%%F"
)

if not defined ENTRY (
  call :log "ERROR: Could not find a known Python entry file."
  echo ERROR: Could not find a known Python entry file in:
  echo   "%APP_DIR%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

set "MODULE="
if /I "%ENTRY%"=="app\main.py" set "MODULE=app.launcher_entry"
if /I "%ENTRY%"=="app\app.py" set "MODULE=app.app"
if /I "%ENTRY%"=="app\run.py" set "MODULE=app.run"
if /I "%ENTRY%"=="app\ar_camera_ollama.py" set "MODULE=app.ar_camera_ollama"
if /I "%ENTRY%"=="app\AR_Camera_Ollama.py" set "MODULE=app.AR_Camera_Ollama"
if /I "%ENTRY%"=="app\camera_ollama.py" set "MODULE=app.camera_ollama"
if /I "%ENTRY%"=="src\main.py" set "MODULE=src.main"
if /I "%ENTRY%"=="src\app.py" set "MODULE=src.app"

if /I "%MODULE%"=="app.launcher_entry" (
  if not exist "%PATCH_APP%\launcher_entry.py" if not exist "%APP_DIR%\app\launcher_entry.py" (
    set "MODULE=app.main"
    call :log "launcher_entry missing; starting app.main without patch hook."
  ) else (
    call :log "Using launcher entry with LOCALAPPDATA patch override."
  )
)

set "PYTHONPATH=%PATCH_RUNTIME%;%APP_DIR%"
call :log "PYTHONPATH=%PYTHONPATH%"

if defined MODULE (
  call :log "Starting entry module: %MODULE%"
  "%VENV_PY%" -m "%MODULE%" >> "%LOG_FILE%" 2>&1
) else (
  call :log "Starting entry file: %ENTRY%"
  "%VENV_PY%" "%APP_DIR%\%ENTRY%" >> "%LOG_FILE%" 2>&1
)
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  call :log "ERROR: App exited with code %EXIT_CODE%."
  echo.
  echo App exited with code %EXIT_CODE%.
  echo Log: "%LOG_FILE%"
  echo.
  echo Last log lines:
  powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path $env:LOG_FILE) { Get-Content $env:LOG_FILE -Tail 30 }"
  echo.
  pause
  exit /b %EXIT_CODE%
)

call :log "App exited successfully."
exit /b 0

:sync_patch_modules
call :log "Syncing patch modules from GitHub to LOCALAPPDATA..."
for %%F in (patch_sync.py launcher_entry.py home_menu_patch.py ar_imaging_adjustment.py ai_experiment_llm_judgement.py experiment_shared.py ollama_vision_client.py jbd4020_cast_support.py ai_experiment_judgement.py) do (
  call :download_patch_file %%F
)
exit /b 0

:download_patch_file
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$u='%PATCH_RAW%/%~1';" ^
  "$o='%PATCH_APP%\%~1';" ^
  "try { Invoke-WebRequest -Uri $u -OutFile $o -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 call :log "  patch synced: %~1"
exit /b 0

:log
echo [%date% %time%] %~1
>> "%LOG_FILE%" echo [%date% %time%] %~1
exit /b 0
