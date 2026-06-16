@echo off
setlocal EnableExtensions

set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%.") do set "SOURCE_DIR=%%~fI"
set "PROJECT_DIR=%~1"
set "FIXED_DIR=%~2"

if not defined PROJECT_DIR set "PROJECT_DIR=C:\Users\lodge\AR_Camera_Ollama"
if not defined FIXED_DIR set "FIXED_DIR=D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix"

for %%I in ("%PROJECT_DIR%.") do set "PROJECT_DIR=%%~fI"
for %%I in ("%FIXED_DIR%.") do set "FIXED_DIR=%%~fI"

set "FEATURE_FILE=%SOURCE_DIR%feature\ai_experiment_judgement\app\ai_experiment_judgement.py"
set "PATCH_FILE=%SOURCE_DIR%feature\ai_experiment_judgement\app\home_menu_patch.py"
set "ENTRY_FILE=%SOURCE_DIR%feature\ai_experiment_judgement\app\launcher_entry.py"
set "MAIN_LAUNCHER_FILE=%SOURCE_DIR%tools\windows\launch_ar_camera_ollama.bat"
set "FEATURE_LAUNCHER_FILE=%SOURCE_DIR%tools\windows\launch_ai_experiment_judgement.bat"
set "MENU_PATCHER=%SOURCE_DIR%tools\windows\patch_main_menu_button_05.py"

echo Installing AI experiment judgement feature...
echo Project:
echo   "%PROJECT_DIR%"
echo Fixed source:
echo   "%FIXED_DIR%"
echo.

if not exist "%FEATURE_FILE%" (
  echo ERROR: Missing feature file:
  echo   "%FEATURE_FILE%"
  pause
  exit /b 1
)

if not exist "%PATCH_FILE%" (
  echo ERROR: Missing home menu patch file:
  echo   "%PATCH_FILE%"
  pause
  exit /b 1
)

if not exist "%MAIN_LAUNCHER_FILE%" (
  echo ERROR: Missing main launcher file:
  echo   "%MAIN_LAUNCHER_FILE%"
  pause
  exit /b 1
)

if not exist "%FEATURE_LAUNCHER_FILE%" (
  echo ERROR: Missing feature launcher file:
  echo   "%FEATURE_LAUNCHER_FILE%"
  pause
  exit /b 1
)

call :install_to "%PROJECT_DIR%"
if errorlevel 1 exit /b 1

if exist "%FIXED_DIR%\" (
  call :install_to "%FIXED_DIR%"
  if errorlevel 1 exit /b 1
) else (
  echo Fixed source folder not found; skipped:
  echo   "%FIXED_DIR%"
)

echo.
echo AI experiment judgement feature copied.
echo.
echo Test from project root:
echo   launch_ai_experiment_judgement.bat
echo.
echo To add the home page button, run:
echo   安装首页05按钮.bat
echo.
pause
exit /b 0

:install_to
set "TARGET=%~1"
if not exist "%TARGET%\" (
  echo ERROR: Target folder does not exist:
  echo   "%TARGET%"
  pause
  exit /b 1
)
if not exist "%TARGET%\app" mkdir "%TARGET%\app" >nul 2>&1
copy /Y "%FEATURE_FILE%" "%TARGET%\app\ai_experiment_judgement.py" >nul
if errorlevel 1 (
  echo ERROR: Could not copy feature module to:
  echo   "%TARGET%\app"
  pause
  exit /b 1
)
copy /Y "%PATCH_FILE%" "%TARGET%\app\home_menu_patch.py" >nul
if errorlevel 1 (
  echo ERROR: Could not copy home menu patch to:
  echo   "%TARGET%\app"
  pause
  exit /b 1
)
if exist "%ENTRY_FILE%" (
  copy /Y "%ENTRY_FILE%" "%TARGET%\app\launcher_entry.py" >nul
  if errorlevel 1 (
    echo ERROR: Could not copy launcher entry to:
    echo   "%TARGET%\app"
    pause
    exit /b 1
  )
)
copy /Y "%MAIN_LAUNCHER_FILE%" "%TARGET%\launch_ar_camera_ollama.bat" >nul
if errorlevel 1 (
  echo ERROR: Could not copy main launcher to:
  echo   "%TARGET%"
  pause
  exit /b 1
)
copy /Y "%FEATURE_LAUNCHER_FILE%" "%TARGET%\launch_ai_experiment_judgement.bat" >nul
if errorlevel 1 (
  echo ERROR: Could not copy feature launcher to:
  echo   "%TARGET%"
  pause
  exit /b 1
)
if exist "%SOURCE_DIR%tools\windows\start_app.bat" (
  copy /Y "%SOURCE_DIR%tools\windows\start_app.bat" "%TARGET%\start_app.bat" >nul
  if errorlevel 1 (
    echo ERROR: Could not copy start_app.bat to:
    echo   "%TARGET%"
    pause
    exit /b 1
  )
)
echo Installed feature into: "%TARGET%"
exit /b 0
