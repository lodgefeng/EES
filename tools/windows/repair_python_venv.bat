@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "APP_DIR=%~dp0"
for %%I in ("%APP_DIR%.") do set "APP_DIR=%%~fI"
set "VENV_DIR=%APP_DIR%\python_venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "NEED_RECREATE=0"
set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LOG_FILE=%LOG_DIR%\repair_python_venv.log"
set "LAUNCHER=%APP_DIR%\launch_ar_camera_ollama.bat"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

call :log "Repair started."
call :log "App directory: %APP_DIR%"

cd /d "%APP_DIR%" || (
  call :log "ERROR: Could not change to app directory."
  echo ERROR: Could not change to "%APP_DIR%".
  pause
  exit /b 1
)

if exist "%VENV_PY%" (
  call :log "Existing virtual environment found."
  "%VENV_PY%" -c "import sys; print(sys.executable)" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "WARNING: Existing python_venv is not usable."
    set "NEED_RECREATE=1"
  ) else (
    goto install_requirements
  )
)

if exist "%VENV_DIR%" if not exist "%VENV_PY%" (
  call :log "WARNING: python_venv exists but Scripts\python.exe is missing."
  set "NEED_RECREATE=1"
)

call :find_python
if not defined PY_CMD (
  call :log "ERROR: Could not find Python. Install Python 3.9+ and enable the py launcher or PATH."
  echo ERROR: Could not find Python.
  echo.
  echo Install Python 3.9 or newer from https://www.python.org/downloads/windows/
  echo During installation, enable "Add python.exe to PATH".
  echo.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

call :log "Using Python command: %PY_CMD%"

if "%NEED_RECREATE%"=="1" (
  set "BACKUP_DIR=%APP_DIR%\python_venv_broken_%RANDOM%"
  call :log "Backing up broken virtual environment to: !BACKUP_DIR!"
  move "%VENV_DIR%" "!BACKUP_DIR!" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "ERROR: Could not move broken python_venv out of the way."
    echo ERROR: Could not move broken python_venv.
    echo.
    echo Close any running AR_Camera_Ollama windows and run this file as Administrator.
    echo Log: "%LOG_FILE%"
    pause
    exit /b 1
  )
)

if not exist "%VENV_DIR%" (
  call :log "Creating virtual environment: %VENV_DIR%"
  %PY_CMD% -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "ERROR: Failed to create python_venv."
    echo ERROR: Failed to create python_venv.
    echo.
    echo If this app is installed under Program Files, run this file as Administrator,
    echo or reinstall the app into a writable folder such as:
    echo   %LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama
    echo.
    echo Log: "%LOG_FILE%"
    pause
    exit /b 1
  )
)

if not exist "%VENV_PY%" (
  call :log "ERROR: Virtual environment was created but python.exe is missing."
  echo ERROR: "%VENV_PY%" does not exist.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

:install_requirements
call :log "Upgrading pip."
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :log "ERROR: Failed to upgrade pip."
  echo ERROR: Failed to upgrade pip.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

set "REQ_FOUND=0"
if exist "%APP_DIR%\requirements.txt" (
  set "REQ_FOUND=1"
  call :install_requirements_file "%APP_DIR%\requirements.txt"
  if errorlevel 1 exit /b 1
)
if exist "%APP_DIR%\app\requirements.txt" (
  set "REQ_FOUND=1"
  call :install_requirements_file "%APP_DIR%\app\requirements.txt"
  if errorlevel 1 exit /b 1
)
if exist "%APP_DIR%\requirements\*.txt" (
  for %%R in ("%APP_DIR%\requirements\*.txt") do (
    set "REQ_FOUND=1"
    call :install_requirements_file "%%~fR"
    if errorlevel 1 exit /b 1
  )
)

if "%REQ_FOUND%"=="0" call :log "No requirements.txt found; checking common runtime packages."

call :ensure_python_package "cv2" "opencv-python"
if errorlevel 1 exit /b 1

call :ensure_python_package "PIL" "pillow"
if errorlevel 1 exit /b 1

call :ensure_python_package "requests" "requests"
if errorlevel 1 exit /b 1

call :ensure_python_package "serial" "pyserial"
if errorlevel 1 exit /b 1

call :ensure_python_package "PySide6" "PySide6"
if errorlevel 1 exit /b 1

call :ensure_python_package "numpy" "numpy"
if errorlevel 1 exit /b 1

if exist "%LAUNCHER%" (
  call :log "Creating desktop shortcut."
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$shortcutPath = [IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'AR Camera Ollama.lnk'); $shell = New-Object -ComObject WScript.Shell; $shortcut = $shell.CreateShortcut($shortcutPath); $shortcut.TargetPath = $env:LAUNCHER; $shortcut.WorkingDirectory = $env:APP_DIR; $shortcut.Save()" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "WARNING: Could not create desktop shortcut."
  )
) else (
  call :log "Launcher not found; skipping desktop shortcut creation."
)

call :log "Repair completed successfully."
echo.
echo Repair completed successfully.
echo Log: "%LOG_FILE%"
echo.
echo If the desktop shortcut still does not start the app, run:
echo   "%LAUNCHER%"
echo.
pause
exit /b 0

:install_requirements_file
set "REQ_FILE=%~1"
call :log "Installing requirements file: %REQ_FILE%"
"%VENV_PY%" -m pip install -r "%REQ_FILE%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :log "ERROR: Failed to install requirements file: %REQ_FILE%"
  echo ERROR: Failed to install requirements file:
  echo   "%REQ_FILE%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
exit /b 0

:ensure_python_package
set "IMPORT_NAME=%~1"
set "PACKAGE_NAME=%~2"
"%VENV_PY%" -c "import %IMPORT_NAME%" >nul 2>&1
if not errorlevel 1 (
  call :log "Python package already available: %IMPORT_NAME%"
  exit /b 0
)
call :log "Installing missing Python package: %PACKAGE_NAME% for import %IMPORT_NAME%"
"%VENV_PY%" -m pip install "%PACKAGE_NAME%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :log "ERROR: Failed to install Python package: %PACKAGE_NAME%"
  echo ERROR: Failed to install Python package:
  echo   "%PACKAGE_NAME%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
exit /b 0

:find_python
set "PY_CMD="
for %%C in ("py -3.11" "py -3.10" "py -3.9" "py -3" "python" "python3") do (
  if not defined PY_CMD (
    %%~C -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY_CMD=%%~C"
  )
)
exit /b 0

:log
echo [%date% %time%] %~1
>> "%LOG_FILE%" echo [%date% %time%] %~1
exit /b 0
