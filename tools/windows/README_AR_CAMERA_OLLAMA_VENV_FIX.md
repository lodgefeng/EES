# AR_Camera_Ollama Windows python_venv repair

The current repository does not contain the AR_Camera_Ollama source code, so
these helper scripts are designed to be copied into the installed app folder:

```text
C:\Program Files\Creolight\AR_Camera_Ollama
```

## Files

- `install_fixed_ar_camera_ollama.bat`
  - Integrates the already-fixed app folder into a repeatable installer flow for
    new Windows machines.
  - Defaults to this fixed source folder:

    ```text
    D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
    ```

  - Installs to this per-user folder by default:

    ```text
    %LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama
    ```

  - Copies the fixed app files, excluding non-portable virtual environments
    such as `python_venv`, `.venv`, and `venv`.
  - Copies the launcher/repair helpers into the install folder.
  - Runs `repair_python_venv.bat` in the install folder to create a clean venv
    for the new computer.
  - Writes an install log to:

    ```text
    %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\install_fixed_build.log
    ```

- `repair_python_venv.bat`
  - Finds Python 3.9 or newer.
  - Creates `python_venv` if it is missing.
  - Upgrades pip/setuptools/wheel.
  - Installs `requirements.txt` if the app folder has one.
  - Creates a desktop shortcut named `AR Camera Ollama.lnk` that starts in the
    app folder.
  - Writes a repair log to:

    ```text
    %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\repair_python_venv.log
    ```

- `launch_ar_camera_ollama.bat`
  - Always changes the working directory to the app folder first.
  - Starts the app using `python_venv\Scripts\python.exe`.
  - Shows errors instead of failing silently when launched from a desktop
    shortcut.
  - Writes a launcher log to:

    ```text
    %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\launcher.log
    ```

## How to use on the Windows machine

### New computer install from the fixed folder

Use this flow for future new-computer installs after copying the repaired app
folder to:

```text
D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
```

1. Keep these helper files together in one folder:

   ```text
   install_fixed_ar_camera_ollama.bat
   repair_python_venv.bat
   launch_ar_camera_ollama.bat
   README_AR_CAMERA_OLLAMA_VENV_FIX.md
   ```

2. Double-click or run:

   ```text
   install_fixed_ar_camera_ollama.bat
   ```

   The script uses `D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix` as the source
   automatically.

3. To use a different fixed source folder:

   ```text
   install_fixed_ar_camera_ollama.bat "E:\path\to\AR_Camera_Ollama_fix"
   ```

4. To choose both source and install folder:

   ```text
   install_fixed_ar_camera_ollama.bat "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix" "%LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama"
   ```

The default install path is under `%LOCALAPPDATA%` so the app can create and
repair `python_venv` without requiring Administrator permissions.

### Repair an already-installed copy

1. Copy these two files into:

   ```text
   C:\Program Files\Creolight\AR_Camera_Ollama
   ```

2. Right-click `repair_python_venv.bat` and choose **Run as administrator**.

   Administrator permissions are often required because `Program Files` is not
   writable by normal users.

3. After repair finishes, start the app using either:

   ```text
   launch_ar_camera_ollama.bat
   ```

   or the new desktop shortcut named:

   ```text
   AR Camera Ollama
   ```

## If it still does not start

Open this log and check the last error:

```text
%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\launcher.log
```

The launcher auto-detects common entry files:

```text
main.py
app.py
run.py
ar_camera_ollama.py
AR_Camera_Ollama.py
camera_ollama.py
```

If the app uses a different entry file, edit `launch_ar_camera_ollama.bat` and
set the `ENTRY` value to the correct Python file.

## Recommended installer fix

For a permanent fix in the real project installer:

1. Make the desktop shortcut target `launch_ar_camera_ollama.bat`.
2. Set the shortcut "Start in" directory to:

   ```text
   C:\Program Files\Creolight\AR_Camera_Ollama
   ```

3. If the app creates `python_venv` at first launch, install the app to a
   writable per-user folder instead of `Program Files`, or run the installer
   with elevated permissions and create the venv during installation.
