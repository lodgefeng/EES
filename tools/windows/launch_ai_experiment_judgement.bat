@echo off
setlocal EnableExtensions

set "APP_DIR=%~dp0"
for %%I in ("%APP_DIR%.") do set "APP_DIR=%%~fI"
set "VENV_PY=%APP_DIR%\python_venv\Scripts\python.exe"
set "REPAIR=%APP_DIR%\repair_python_venv.bat"

cd /d "%APP_DIR%" || (
  echo ERROR: Could not change to "%APP_DIR%".
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  if exist "%REPAIR%" call "%REPAIR%"
)

if not exist "%VENV_PY%" (
  echo ERROR: "%VENV_PY%" does not exist.
  pause
  exit /b 1
)

"%VENV_PY%" -m app.ai_experiment_judgement
if errorlevel 1 pause
exit /b %ERRORLEVEL%
