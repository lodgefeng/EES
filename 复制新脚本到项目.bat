@echo off
setlocal EnableExtensions

set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR=%%~fI"
set "TARGET_DIR=%~1"

if not defined TARGET_DIR set "TARGET_DIR=C:\Users\lodge\AR_Camera_Ollama"
for %%I in ("%TARGET_DIR%.") do set "TARGET_DIR=%%~fI"

set "TARGET_TOOLS=%TARGET_DIR%\tools\windows"

echo Copying AR_Camera_Ollama helper scripts...
echo Source:
echo   "%SOURCE_DIR%"
echo Target:
echo   "%TARGET_DIR%"
echo.

if not exist "%TARGET_DIR%\" (
  echo ERROR: Target project folder does not exist:
  echo   "%TARGET_DIR%"
  echo.
  echo Usage:
  echo   copy-new-scripts.bat "C:\Users\lodge\AR_Camera_Ollama"
  echo.
  pause
  exit /b 1
)

if not exist "%SOURCE_DIR%tools\windows\" (
  echo ERROR: Missing source tools folder:
  echo   "%SOURCE_DIR%tools\windows"
  echo.
  echo Keep this script together with build_ar_camera_ollama_installer.bat
  echo and the tools\windows folder.
  echo.
  pause
  exit /b 1
)

if not exist "%TARGET_DIR%\tools" mkdir "%TARGET_DIR%\tools" >nul 2>&1
if not exist "%TARGET_TOOLS%" mkdir "%TARGET_TOOLS%" >nul 2>&1

for %%F in ("%SOURCE_DIR%*.bat") do (
  copy /Y "%%~fF" "%TARGET_DIR%\%%~nxF" >nul
  if errorlevel 1 (
    echo ERROR: Could not copy root file: %%~nxF
    pause
    exit /b 1
  )
  echo Copied root file: %%~nxF
)

call :copy_tool "build_ar_camera_ollama_installer.bat"
if errorlevel 1 exit /b 1

call :copy_tool "package_install_ar_camera_ollama.bat"
if errorlevel 1 exit /b 1

call :copy_tool "repair_python_venv.bat"
if errorlevel 1 exit /b 1

call :copy_tool "launch_ar_camera_ollama.bat"
if errorlevel 1 exit /b 1

call :copy_tool "install_fixed_ar_camera_ollama.bat"
if errorlevel 1 exit /b 1

call :copy_tool "sync_fixed_build_to_project.bat"
if errorlevel 1 exit /b 1

call :copy_tool "README_AR_CAMERA_OLLAMA_VENV_FIX.md"
if errorlevel 1 exit /b 1

call :copy_ai_feature "%TARGET_DIR%"
if errorlevel 1 exit /b 1

if exist "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix\" (
  call :copy_ai_feature "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix"
  if errorlevel 1 exit /b 1
)

echo.
echo Done.
echo.
echo Now run this from the project root:
echo   the no-python-check package script
echo.
pause
exit /b 0

:copy_tool
set "FILE_NAME=%~1"
if not exist "%SOURCE_DIR%tools\windows\%FILE_NAME%" (
  echo ERROR: Missing source tool:
  echo   "%SOURCE_DIR%tools\windows\%FILE_NAME%"
  pause
  exit /b 1
)
copy /Y "%SOURCE_DIR%tools\windows\%FILE_NAME%" "%TARGET_TOOLS%\%FILE_NAME%" >nul
if errorlevel 1 (
  echo ERROR: Could not copy %FILE_NAME% to tools\windows.
  pause
  exit /b 1
)
echo Copied tool file: %FILE_NAME%
exit /b 0

:copy_ai_feature
set "FEATURE_TARGET=%~1"
set "FEATURE_SOURCE=%SOURCE_DIR%feature\ai_experiment_judgement\app\ai_experiment_judgement.py"
if not exist "%FEATURE_SOURCE%" exit /b 0
if not exist "%FEATURE_TARGET%\app" mkdir "%FEATURE_TARGET%\app" >nul 2>&1
copy /Y "%FEATURE_SOURCE%" "%FEATURE_TARGET%\app\ai_experiment_judgement.py" >nul
if errorlevel 1 (
  echo ERROR: Could not copy AI experiment feature to:
  echo   "%FEATURE_TARGET%\app"
  pause
  exit /b 1
)
if exist "%SOURCE_DIR%tools\windows\launch_ai_experiment_judgement.bat" (
  copy /Y "%SOURCE_DIR%tools\windows\launch_ai_experiment_judgement.bat" "%FEATURE_TARGET%\launch_ai_experiment_judgement.bat" >nul
)
echo Copied AI experiment feature to: "%FEATURE_TARGET%"
exit /b 0
