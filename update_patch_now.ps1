# Creolight menu patch one-click update (no admin)
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$patchRuntime = Join-Path $env:LOCALAPPDATA "Creolight\AR_Camera_Ollama\patch_runtime"
$patchApp = Join-Path $patchRuntime "app"
$startup = Join-Path $patchRuntime "creolight_startup.py"
$launcher = Join-Path $env:LOCALAPPDATA "Creolight\AR_Camera_Ollama\start_patched.bat"
$installDir = "C:\Program Files\Creolight\AR_Camera_Ollama"
$raw = "https://raw.githubusercontent.com/lodgefeng/EES/cursor/fix-python-venv-launch-e627/feature/ai_experiment_judgement/app"

New-Item -ItemType Directory -Force -Path $patchApp | Out-Null

$files = @(
    @{ Name = "creolight_startup.py"; Dest = $startup },
    @{ Name = "home_menu_patch.py"; Dest = (Join-Path $patchApp "home_menu_patch.py") },
    @{ Name = "patch_sync.py"; Dest = (Join-Path $patchApp "patch_sync.py") },
    @{ Name = "launcher_entry.py"; Dest = (Join-Path $patchApp "launcher_entry.py") },
    @{ Name = "ar_imaging_adjustment.py"; Dest = (Join-Path $patchApp "ar_imaging_adjustment.py") },
    @{ Name = "ai_experiment_llm_judgement.py"; Dest = (Join-Path $patchApp "ai_experiment_llm_judgement.py") },
    @{ Name = "experiment_shared.py"; Dest = (Join-Path $patchApp "experiment_shared.py") },
    @{ Name = "ollama_vision_client.py"; Dest = (Join-Path $patchApp "ollama_vision_client.py") },
    @{ Name = "jbd4020_cast_support.py"; Dest = (Join-Path $patchApp "jbd4020_cast_support.py") },
    @{ Name = "ai_experiment_judgement.py"; Dest = (Join-Path $patchApp "ai_experiment_judgement.py") },
    @{ Name = "run_patched_app.py"; Dest = (Join-Path $patchRuntime "run_patched_app.py") }
)

Write-Host "================================================"
Write-Host "Creolight patch update v2 (PYTHONSTARTUP)"
Write-Host "================================================"
Write-Host ""

foreach ($item in $files) {
    Invoke-WebRequest -Uri "$raw/$($item.Name)" -OutFile $item.Dest -UseBasicParsing
    Write-Host "[OK] $($item.Dest)"
}

if (-not (Test-Path $startup)) {
    throw "creolight_startup.py missing after download"
}

$bat = @"
@echo off
setlocal EnableExtensions
set "APP_DIR=$installDir"
set "PATCH_RUNTIME=$patchRuntime"
set "CREOLIGHT_APP_DIR=%APP_DIR%"
set "CREOLIGHT_PATCH_RUNTIME=%PATCH_RUNTIME%"
set "PYTHONSTARTUP=%PATCH_RUNTIME%\creolight_startup.py"
set "LOG_DIR=%LOCALAPPDATA%\Creolight\AR_Camera_Ollama"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1
cd /d "%APP_DIR%"
"%APP_DIR%\python_venv\Scripts\python.exe" -m app.main >> "%LOG_DIR%\launcher.log" 2>&1
if errorlevel 1 pause
"@

Set-Content -Path $launcher -Value $bat -Encoding ASCII
Write-Host ""
Write-Host "SUCCESS."
Write-Host "Required file OK:"
Write-Host "  $startup"
Write-Host ""
Write-Host "Start app with:"
Write-Host "  $launcher"
Write-Host ""
Read-Host "Press Enter to close"
