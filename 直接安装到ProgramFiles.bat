@echo off
setlocal EnableExtensions

set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"
set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR=%%~fI"
set "PATCH_APP=%SOURCE_DIR%feature\ai_experiment_judgement\app"
set "INSTALLER=%SOURCE_DIR%tools\windows\install_patch_to_program_files.py"

echo ================================================
echo Creolight direct install (recommended)
echo ================================================
echo.

net session >nul 2>&1
if errorlevel 1 (
  echo Need administrator to copy into:
  echo   "%INSTALL_DIR%\app"
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

if not exist "%INSTALL_DIR%\app\main.py" (
  echo ERROR: missing "%INSTALL_DIR%\app\main.py"
  pause
  exit /b 1
)

if not exist "%PATCH_APP%\bootstrap_main.py" (
  echo ERROR: patch source not found:
  echo   "%PATCH_APP%"
  pause
  exit /b 1
)

if not exist "%INSTALL_DIR%\python_venv\Scripts\python.exe" (
  echo ERROR: missing Python venv in install dir
  pause
  exit /b 1
)

echo Installing patch modules from local repo...
"%INSTALL_DIR%\python_venv\Scripts\python.exe" "%INSTALLER%" "%INSTALL_DIR%" "%PATCH_APP%"
if errorlevel 1 (
  echo ERROR: install script failed
  pause
  exit /b 1
)

echo.
echo Verifying required files...
set "FAILED=0"
call :check "%INSTALL_DIR%\app\bootstrap_main.py"
call :check "%INSTALL_DIR%\app\home_menu_patch.py"
call :check "%INSTALL_DIR%\app\ar_imaging_adjustment.py"
call :check "%INSTALL_DIR%\app\ai_experiment_llm_judgement.py"
call :check "%INSTALL_DIR%\start_app.bat"

if not "%FAILED%"=="0" (
  echo ERROR: verification failed
  pause
  exit /b 1
)

echo.
echo SUCCESS.
echo Close the app completely, then start it again from the Creolight shortcut.
echo You should see buttons 05 and 06 on the home page, or a small top window.
echo Log: %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\launcher.log
echo.
pause
exit /b 0

:check
if exist "%~1" (
  echo   [OK] %~1
) else (
  echo   [MISSING] %~1
  set "FAILED=1"
)
exit /b 0
