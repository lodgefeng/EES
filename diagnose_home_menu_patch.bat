@echo off
setlocal EnableExtensions

set "INSTALL_DIR=C:\Program Files\Creolight\AR_Camera_Ollama"
set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
set "LAUNCHER_LOG=%LOG_DIR%\launcher.log"
set "PATCH_LOG=%LOG_DIR%\home_menu_patch.log"

echo ========================================
echo Creolight home menu patch diagnostic
echo ========================================
echo.

echo [1] Install folder
if exist "%INSTALL_DIR%\app\main.py" (
  echo   [OK] %INSTALL_DIR%
) else (
  echo   [MISSING] %INSTALL_DIR%\app\main.py
)
echo.

echo [2] Patch files
call :check "%INSTALL_DIR%\app\home_menu_patch.py"
call :check "%INSTALL_DIR%\app\launcher_entry.py"
call :check "%INSTALL_DIR%\app\ar_imaging_adjustment.py"
call :check "%INSTALL_DIR%\app\ai_experiment_llm_judgement.py"
call :check "%INSTALL_DIR%\start_app.bat"
echo.

echo [3] start_app.bat launcher hook
findstr /I /C:"launcher_entry" "%INSTALL_DIR%\start_app.bat" >nul
if errorlevel 1 (
  echo   [BAD] start_app.bat does not use app.launcher_entry
  echo         Run fix_program_files_button_05.bat as administrator.
) else (
  echo   [OK] start_app.bat uses app.launcher_entry
)
echo.

echo [4] Desktop shortcut target
set "SHORTCUT=%USERPROFILE%\Desktop\光创元 AI+AR教学实验系统.lnk"
if not exist "%SHORTCUT%" set "SHORTCUT=%USERPROFILE%\Desktop\AR_Camera_Ollama.lnk"
if exist "%SHORTCUT%" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%'); Write-Host ('  Target: ' + $s.TargetPath); Write-Host ('  Args: ' + $s.Arguments)"
) else (
  echo   [WARN] Desktop shortcut not found on Desktop
)
echo.

echo [5] launcher.log last lines
if exist "%LAUNCHER_LOG%" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content '%LAUNCHER_LOG%' -Tail 20"
) else (
  echo   [MISSING] %LAUNCHER_LOG%
)
echo.

echo [6] home_menu_patch.log last lines
if exist "%PATCH_LOG%" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content '%PATCH_LOG%' -Tail 30"
) else (
  echo   [MISSING] %PATCH_LOG%
  echo   This usually means the patch runtime never started.
)
echo.
pause
exit /b 0

:check
if exist "%~1" (
  echo   [OK] %~1
) else (
  echo   [MISSING] %~1
)
exit /b 0
