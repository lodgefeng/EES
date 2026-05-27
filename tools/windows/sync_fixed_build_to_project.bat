@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "DEFAULT_FIXED_SOURCE=D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix"
set "DEFAULT_PROJECT_DIR=C:\Users\lodge\AR_Camera_Ollama"
set "FIXED_SOURCE=%~1"
set "PROJECT_DIR=%~2"
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%.") do set "SCRIPT_DIR=%%~fI"

if not defined FIXED_SOURCE set "FIXED_SOURCE=%AR_CAMERA_FIXED_SOURCE%"
if not defined FIXED_SOURCE set "FIXED_SOURCE=%DEFAULT_FIXED_SOURCE%"
if not defined PROJECT_DIR set "PROJECT_DIR=%AR_CAMERA_PROJECT_DIR%"
if not defined PROJECT_DIR set "PROJECT_DIR=%DEFAULT_PROJECT_DIR%"

for %%I in ("%FIXED_SOURCE%.") do set "FIXED_SOURCE=%%~fI"
for %%I in ("%PROJECT_DIR%.") do set "PROJECT_DIR=%%~fI"

set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LOG_FILE=%LOG_DIR%\sync_fixed_build_to_project.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

call :log "Project sync started."
call :log "Fixed source: %FIXED_SOURCE%"
call :log "Project directory: %PROJECT_DIR%"

if /I "%FIXED_SOURCE%"=="%PROJECT_DIR%" (
  call :log "ERROR: Fixed source and project directory must be different."
  echo ERROR: Fixed source and project directory must be different.
  echo.
  echo Fixed source:
  echo   "%FIXED_SOURCE%"
  echo Project directory:
  echo   "%PROJECT_DIR%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

if not exist "%FIXED_SOURCE%\" (
  call :log "ERROR: Fixed source directory does not exist."
  echo ERROR: Fixed source directory does not exist:
  echo   "%FIXED_SOURCE%"
  echo.
  echo Usage:
  echo   sync_fixed_build_to_project.bat "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix" "C:\Users\lodge\AR_Camera_Ollama"
  echo.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

if not exist "%PROJECT_DIR%\" (
  call :log "Creating project directory."
  mkdir "%PROJECT_DIR%" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "ERROR: Could not create project directory."
    echo ERROR: Could not create project directory:
    echo   "%PROJECT_DIR%"
    echo Log: "%LOG_FILE%"
    pause
    exit /b 1
  )
)

call :log "Copying fixed files into project directory."
robocopy "%FIXED_SOURCE%" "%PROJECT_DIR%" /E /XD python_venv venv .venv __pycache__ .git build dist /XF *.pyc /R:2 /W:2 /NP /TEE /LOG+:"%LOG_FILE%"
set "ROBOCOPY_EXIT=%ERRORLEVEL%"
if %ROBOCOPY_EXIT% GEQ 8 (
  call :log "ERROR: Robocopy failed with code %ROBOCOPY_EXIT%."
  echo ERROR: Failed to sync fixed files into the project.
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

call :copy_helper "install_fixed_ar_camera_ollama.bat"
if errorlevel 1 exit /b 1

call :copy_helper "README_AR_CAMERA_OLLAMA_VENV_FIX.md"
if errorlevel 1 exit /b 1

call :log "Running python_venv repair in project directory."
call "%PROJECT_DIR%\repair_python_venv.bat"
set "REPAIR_EXIT=%ERRORLEVEL%"
if not "%REPAIR_EXIT%"=="0" (
  call :log "ERROR: repair_python_venv.bat failed with code %REPAIR_EXIT%."
  echo ERROR: python_venv repair failed.
  echo Log: "%LOG_FILE%"
  pause
  exit /b %REPAIR_EXIT%
)

call :log "Project sync completed successfully."
echo.
echo Project sync completed successfully.
echo Project directory:
echo   "%PROJECT_DIR%"
echo.
echo The project now contains the fixed files and helper launch scripts.
echo Use this launcher from the project root:
echo   "%PROJECT_DIR%\launch_ar_camera_ollama.bat"
echo.
echo Log: "%LOG_FILE%"
pause
exit /b 0

:copy_helper
set "HELPER_NAME=%~1"
if not exist "%SCRIPT_DIR%\%HELPER_NAME%" (
  call :log "ERROR: Missing helper next to sync script: %HELPER_NAME%"
  echo ERROR: Missing helper next to sync script:
  echo   "%SCRIPT_DIR%\%HELPER_NAME%"
  echo.
  echo Keep sync_fixed_build_to_project.bat together with the other helper files in tools\windows.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
copy /Y "%SCRIPT_DIR%\%HELPER_NAME%" "%PROJECT_DIR%\%HELPER_NAME%" >> "%LOG_FILE%" 2>&1
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
