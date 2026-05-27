@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "PACKAGE_DIR=%~dp0"
for %%I in ("%PACKAGE_DIR%.") do set "PACKAGE_DIR=%%~fI"
set "APP_SOURCE=%PACKAGE_DIR%\app"
set "DEFAULT_INSTALL=%LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama"
set "INSTALL_DIR=%~1"

if not defined INSTALL_DIR set "INSTALL_DIR=%AR_CAMERA_INSTALL_DIR%"
if not defined INSTALL_DIR set "INSTALL_DIR=%DEFAULT_INSTALL%"
for %%I in ("%INSTALL_DIR%.") do set "INSTALL_DIR=%%~fI"

set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LOG_FILE=%LOG_DIR%\package_install.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

call :log "Package install started."
call :log "Package directory: %PACKAGE_DIR%"
call :log "App source: %APP_SOURCE%"
call :log "Install directory: %INSTALL_DIR%"

if not exist "%APP_SOURCE%\" (
  call :log "ERROR: Package app folder is missing."
  echo ERROR: Package app folder is missing:
  echo   "%APP_SOURCE%"
  echo.
  echo Make sure you copied the whole AR_Camera_Ollama_installer folder,
  echo including the app subfolder.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

if /I "%APP_SOURCE%"=="%INSTALL_DIR%" (
  call :log "ERROR: Package app source and install directory must be different."
  echo ERROR: Package app source and install directory must be different.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

if not exist "%INSTALL_DIR%" (
  call :log "Creating install directory."
  mkdir "%INSTALL_DIR%" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "ERROR: Could not create install directory."
    echo ERROR: Could not create install directory:
    echo   "%INSTALL_DIR%"
    echo Log: "%LOG_FILE%"
    pause
    exit /b 1
  )
)

call :log "Copying app payload into install directory."
robocopy "%APP_SOURCE%" "%INSTALL_DIR%" /MIR /XD python_venv venv .venv __pycache__ .git /XF *.pyc /R:2 /W:2 /NP /TEE /LOG+:"%LOG_FILE%"
set "ROBOCOPY_EXIT=%ERRORLEVEL%"
if %ROBOCOPY_EXIT% GEQ 8 (
  call :log "ERROR: Robocopy failed with code %ROBOCOPY_EXIT%."
  echo ERROR: Failed to copy app payload.
  echo Robocopy exit code: %ROBOCOPY_EXIT%
  echo Log: "%LOG_FILE%"
  pause
  exit /b %ROBOCOPY_EXIT%
)
call :log "Robocopy completed with code %ROBOCOPY_EXIT%."

call :copy_helper "repair_python_venv.bat"
if errorlevel 1 exit /b 1

call :copy_helper "launch_ar_camera_ollama.bat"
if errorlevel 1 exit /b 1

call :copy_helper "README_AR_CAMERA_OLLAMA_VENV_FIX.md"
if errorlevel 1 exit /b 1

call :log "Running python_venv repair in install directory."
call "%INSTALL_DIR%\repair_python_venv.bat"
set "REPAIR_EXIT=%ERRORLEVEL%"
if not "%REPAIR_EXIT%"=="0" (
  call :log "ERROR: repair_python_venv.bat failed with code %REPAIR_EXIT%."
  echo ERROR: python_venv repair failed.
  echo Log: "%LOG_FILE%"
  pause
  exit /b %REPAIR_EXIT%
)

call :log "Package install completed successfully."
echo.
echo Install completed successfully.
echo Installed to:
echo   "%INSTALL_DIR%"
echo.
echo Use the desktop shortcut "AR Camera Ollama" or run:
echo   "%INSTALL_DIR%\launch_ar_camera_ollama.bat"
echo.
echo Log: "%LOG_FILE%"
pause
exit /b 0

:copy_helper
set "HELPER_NAME=%~1"
if not exist "%PACKAGE_DIR%\%HELPER_NAME%" (
  call :log "ERROR: Missing helper in package: %HELPER_NAME%"
  echo ERROR: Missing helper in package:
  echo   "%PACKAGE_DIR%\%HELPER_NAME%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
copy /Y "%PACKAGE_DIR%\%HELPER_NAME%" "%INSTALL_DIR%\%HELPER_NAME%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :log "ERROR: Could not copy helper: %HELPER_NAME%"
  echo ERROR: Could not copy helper: %HELPER_NAME%
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
call :log "Copied helper: %HELPER_NAME%"
exit /b 0

:log
echo [%date% %time%] %~1
>> "%LOG_FILE%" echo [%date% %time%] %~1
exit /b 0
