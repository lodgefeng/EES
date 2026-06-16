@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "DEFAULT_SOURCE=D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix"
set "DEFAULT_INSTALL=%LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama"
set "SOURCE_DIR=%~1"
set "INSTALL_DIR=%~2"
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%.") do set "SCRIPT_DIR=%%~fI"

if not defined SOURCE_DIR set "SOURCE_DIR=%AR_CAMERA_SOURCE%"
if not defined SOURCE_DIR set "SOURCE_DIR=%DEFAULT_SOURCE%"
if not defined INSTALL_DIR set "INSTALL_DIR=%AR_CAMERA_INSTALL_DIR%"
if not defined INSTALL_DIR set "INSTALL_DIR=%DEFAULT_INSTALL%"

for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR=%%~fI"
for %%I in ("%INSTALL_DIR%.") do set "INSTALL_DIR=%%~fI"

set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LOG_FILE=%LOG_DIR%\install_fixed_build.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

call :log "Install started."
call :log "Source directory: %SOURCE_DIR%"
call :log "Install directory: %INSTALL_DIR%"

if /I "%SOURCE_DIR%"=="%INSTALL_DIR%" (
  call :log "ERROR: Source and install directories must be different."
  echo ERROR: Source and install directories must be different.
  echo.
  echo Source:
  echo   "%SOURCE_DIR%"
  echo Install:
  echo   "%INSTALL_DIR%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

if not exist "%SOURCE_DIR%\" (
  call :log "ERROR: Source directory does not exist."
  echo ERROR: Source directory does not exist:
  echo   "%SOURCE_DIR%"
  echo.
  echo Usage:
  echo   install_fixed_ar_camera_ollama.bat "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix"
  echo.
  echo You can also provide an install directory:
  echo   install_fixed_ar_camera_ollama.bat "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix" "%LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama"
  echo.
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

call :log "Copying fixed app files."
robocopy "%SOURCE_DIR%" "%INSTALL_DIR%" /MIR /XD python_venv venv .venv __pycache__ .git /XF *.pyc /R:2 /W:2 /NP /TEE /LOG+:"%LOG_FILE%"
set "ROBOCOPY_EXIT=%ERRORLEVEL%"
if %ROBOCOPY_EXIT% GEQ 8 (
  call :log "ERROR: Robocopy failed with code %ROBOCOPY_EXIT%."
  echo ERROR: Failed to copy fixed app files.
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

call :log "Install completed successfully."
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
if not exist "%SCRIPT_DIR%\%HELPER_NAME%" (
  call :log "ERROR: Missing helper next to installer: %HELPER_NAME%"
  echo ERROR: Missing helper next to installer:
  echo   "%SCRIPT_DIR%\%HELPER_NAME%"
  echo.
  echo Keep install_fixed_ar_camera_ollama.bat together with the other files in tools\windows.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
copy /Y "%SCRIPT_DIR%\%HELPER_NAME%" "%INSTALL_DIR%\%HELPER_NAME%" >> "%LOG_FILE%" 2>&1
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
