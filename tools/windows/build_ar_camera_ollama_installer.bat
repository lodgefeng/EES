@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "DEFAULT_SOURCE=D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix"
set "DEFAULT_PACKAGE=D:\AR_Camera_Ollama_installer"
set "SOURCE_DIR=%~1"
set "PACKAGE_DIR=%~2"
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%.") do set "SCRIPT_DIR=%%~fI"

if not defined SOURCE_DIR set "SOURCE_DIR=%AR_CAMERA_SOURCE%"
if not defined SOURCE_DIR set "SOURCE_DIR=%DEFAULT_SOURCE%"
if not defined PACKAGE_DIR set "PACKAGE_DIR=%AR_CAMERA_PACKAGE_DIR%"
if not defined PACKAGE_DIR set "PACKAGE_DIR=%DEFAULT_PACKAGE%"

for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR=%%~fI"
for %%I in ("%PACKAGE_DIR%.") do set "PACKAGE_DIR=%%~fI"

set "PAYLOAD_DIR=%PACKAGE_DIR%\app"
set "ZIP_PATH=%PACKAGE_DIR%.zip"
set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LOG_FILE=%LOG_DIR%\build_installer_package.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

call :log "Installer package build started."
call :log "Source directory: %SOURCE_DIR%"
call :log "Package directory: %PACKAGE_DIR%"
call :log "Payload directory: %PAYLOAD_DIR%"
call :log "Zip path: %ZIP_PATH%"

if not exist "%SOURCE_DIR%\" (
  call :log "ERROR: Source directory does not exist."
  echo ERROR: Source directory does not exist:
  echo   "%SOURCE_DIR%"
  echo.
  echo Usage:
  echo   build_ar_camera_ollama_installer.bat "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix" "D:\AR_Camera_Ollama_installer"
  echo.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

if /I "%SOURCE_DIR%"=="%PAYLOAD_DIR%" (
  call :log "ERROR: Source directory and package payload directory must be different."
  echo ERROR: Source directory and package payload directory must be different.
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)

if not exist "%PACKAGE_DIR%" (
  call :log "Creating package directory."
  mkdir "%PACKAGE_DIR%" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "ERROR: Could not create package directory."
    echo ERROR: Could not create package directory:
    echo   "%PACKAGE_DIR%"
    echo Log: "%LOG_FILE%"
    pause
    exit /b 1
  )
)

if not exist "%PAYLOAD_DIR%" mkdir "%PAYLOAD_DIR%" >> "%LOG_FILE%" 2>&1

call :log "Copying app payload into package."
robocopy "%SOURCE_DIR%" "%PAYLOAD_DIR%" /MIR /XD python_venv venv .venv __pycache__ .git /XF *.pyc /R:2 /W:2 /NP /TEE /LOG+:"%LOG_FILE%"
set "ROBOCOPY_EXIT=%ERRORLEVEL%"
if %ROBOCOPY_EXIT% GEQ 8 (
  call :log "ERROR: Robocopy failed with code %ROBOCOPY_EXIT%."
  echo ERROR: Failed to copy app payload into package.
  echo Robocopy exit code: %ROBOCOPY_EXIT%
  echo Log: "%LOG_FILE%"
  pause
  exit /b %ROBOCOPY_EXIT%
)
call :log "Robocopy completed with code %ROBOCOPY_EXIT%."

call :copy_or_generate_installer "install_ar_camera_ollama.bat"
if errorlevel 1 exit /b 1

call :copy_or_generate_installer "install.bat"
if errorlevel 1 exit /b 1

call :copy_package_file "repair_python_venv.bat" "repair_python_venv.bat"
if errorlevel 1 exit /b 1

call :copy_package_file "launch_ar_camera_ollama.bat" "launch_ar_camera_ollama.bat"
if errorlevel 1 exit /b 1

call :copy_package_file "README_AR_CAMERA_OLLAMA_VENV_FIX.md" "README_AR_CAMERA_OLLAMA_VENV_FIX.md"
if errorlevel 1 exit /b 1

call :log "Creating zip package if PowerShell Compress-Archive is available."
if exist "%ZIP_PATH%" del /F /Q "%ZIP_PATH%" >> "%LOG_FILE%" 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path (Join-Path $env:PACKAGE_DIR '*') -DestinationPath $env:ZIP_PATH -Force" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :log "WARNING: Could not create zip package. Folder package is still ready."
) else (
  call :log "Zip package created successfully."
)

call :log "Installer package build completed successfully."
echo.
echo Installer package build completed successfully.
echo Folder package:
echo   "%PACKAGE_DIR%"
echo.
if exist "%ZIP_PATH%" (
  echo Zip package:
  echo   "%ZIP_PATH%"
  echo.
)
echo Copy the folder or zip to the new computer, then run:
echo   install.bat
echo.
echo Log: "%LOG_FILE%"
pause
exit /b 0

:copy_or_generate_installer
set "TARGET_NAME=%~1"
if exist "%SCRIPT_DIR%\package_install_ar_camera_ollama.bat" (
  copy /Y "%SCRIPT_DIR%\package_install_ar_camera_ollama.bat" "%PACKAGE_DIR%\%TARGET_NAME%" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "ERROR: Could not copy package installer template to %TARGET_NAME%"
    echo ERROR: Could not copy package installer template.
    echo Log: "%LOG_FILE%"
    pause
    exit /b 1
  )
  call :log "Copied package installer: %TARGET_NAME%"
  exit /b 0
)

call :log "WARNING: package_install_ar_camera_ollama.bat missing; generating %TARGET_NAME%."
call :write_generated_installer "%PACKAGE_DIR%\%TARGET_NAME%"
exit /b %ERRORLEVEL%

:write_generated_installer
set "TARGET_FILE=%~1"
(
echo @echo off
echo setlocal EnableExtensions
echo set "PACKAGE_DIR=%%~dp0"
echo for %%%%I in ^("%%PACKAGE_DIR%%."^) do set "PACKAGE_DIR=%%%%~fI"
echo set "APP_SOURCE=%%PACKAGE_DIR%%\app"
echo set "INSTALL_DIR=%%~1"
echo if not defined INSTALL_DIR set "INSTALL_DIR=%%LOCALAPPDATA%%\Programs\Creolight\AR_Camera_Ollama"
echo for %%%%I in ^("%%INSTALL_DIR%%."^) do set "INSTALL_DIR=%%%%~fI"
echo set "LOG_DIR=%%LOCALAPPDATA%%\Creolight\AR_Camera_Ollama"
echo set "LOG_FILE=%%LOG_DIR%%\package_install.log"
echo if not exist "%%LOG_DIR%%" mkdir "%%LOG_DIR%%"
echo echo Package install started.
echo if not exist "%%APP_SOURCE%%\" ^(
echo   echo ERROR: Package app folder is missing: "%%APP_SOURCE%%"
echo   pause
echo   exit /b 1
echo ^)
echo if not exist "%%INSTALL_DIR%%" mkdir "%%INSTALL_DIR%%"
echo robocopy "%%APP_SOURCE%%" "%%INSTALL_DIR%%" /MIR /XD python_venv venv .venv __pycache__ .git /XF *.pyc /R:2 /W:2 /NP /TEE /LOG+:"%%LOG_FILE%%"
echo set "ROBOCOPY_EXIT=%%ERRORLEVEL%%"
echo if %%ROBOCOPY_EXIT%% GEQ 8 ^(
echo   echo ERROR: Failed to copy app payload. Robocopy exit code: %%ROBOCOPY_EXIT%%
echo   echo Log: "%%LOG_FILE%%"
echo   pause
echo   exit /b %%ROBOCOPY_EXIT%%
echo ^)
echo copy /Y "%%PACKAGE_DIR%%\repair_python_venv.bat" "%%INSTALL_DIR%%\repair_python_venv.bat"
echo copy /Y "%%PACKAGE_DIR%%\launch_ar_camera_ollama.bat" "%%INSTALL_DIR%%\launch_ar_camera_ollama.bat"
echo if exist "%%PACKAGE_DIR%%\README_AR_CAMERA_OLLAMA_VENV_FIX.md" copy /Y "%%PACKAGE_DIR%%\README_AR_CAMERA_OLLAMA_VENV_FIX.md" "%%INSTALL_DIR%%\README_AR_CAMERA_OLLAMA_VENV_FIX.md"
echo call "%%INSTALL_DIR%%\repair_python_venv.bat"
echo set "REPAIR_EXIT=%%ERRORLEVEL%%"
echo if not "%%REPAIR_EXIT%%"=="0" exit /b %%REPAIR_EXIT%%
echo echo Install completed successfully.
echo echo Installed to: "%%INSTALL_DIR%%"
echo pause
echo exit /b 0
) > "%TARGET_FILE%"
if errorlevel 1 (
  call :log "ERROR: Could not generate package installer: %TARGET_FILE%"
  echo ERROR: Could not generate package installer:
  echo   "%TARGET_FILE%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
call :log "Generated package installer: %TARGET_FILE%"
exit /b 0

:copy_package_file
set "SOURCE_NAME=%~1"
set "TARGET_NAME=%~2"
if not exist "%SCRIPT_DIR%\%SOURCE_NAME%" (
  call :log "ERROR: Missing package helper: %SOURCE_NAME%"
  echo ERROR: Missing package helper:
  echo   "%SCRIPT_DIR%\%SOURCE_NAME%"
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
copy /Y "%SCRIPT_DIR%\%SOURCE_NAME%" "%PACKAGE_DIR%\%TARGET_NAME%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :log "ERROR: Could not copy package file: %SOURCE_NAME% to %TARGET_NAME%"
  echo ERROR: Could not copy package file: %SOURCE_NAME%
  echo Log: "%LOG_FILE%"
  pause
  exit /b 1
)
call :log "Copied package file: %TARGET_NAME%"
exit /b 0

:log
echo [%date% %time%] %~1
>> "%LOG_FILE%" echo [%date% %time%] %~1
exit /b 0
