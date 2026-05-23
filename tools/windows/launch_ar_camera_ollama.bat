@echo off
setlocal EnableExtensions

set "APP_DIR=%~dp0"
for %%I in ("%APP_DIR%.") do set "APP_DIR=%%~fI"
set "VENV_PY=%APP_DIR%\python_venv\Scripts\python.exe"
set "REPAIR=%APP_DIR%\repair_python_venv.bat"
set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LOG_FILE=%LOG_DIR%\launcher.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1
call :log "Launcher started."
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

set "ENTRY="
for %%F in (main.py app.py run.py ar_camera_ollama.py AR_Camera_Ollama.py camera_ollama.py) do (
  if not defined ENTRY if exist "%APP_DIR%\%%F" set "ENTRY=%%F"
)

if not defined ENTRY (
  call :log "ERROR: Could not find a known Python entry file."
  echo ERROR: Could not find a known Python entry file in:
  echo   "%APP_DIR%"
  echo.
  echo Expected one of:
  echo   main.py
  echo   app.py
  echo   run.py
  echo   ar_camera_ollama.py
  echo   AR_Camera_Ollama.py
  echo   camera_ollama.py
  echo.
  echo Edit launch_ar_camera_ollama.bat and set ENTRY to the correct file.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

call :log "Starting entry file: %ENTRY%"
"%VENV_PY%" "%APP_DIR%\%ENTRY%" >> "%LOG_FILE%" 2>&1
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

:log
echo [%date% %time%] %~1
>> "%LOG_FILE%" echo [%date% %time%] %~1
exit /b 0
