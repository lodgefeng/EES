# AR_Camera_Ollama Windows python_venv repair

The current repository does not contain the AR_Camera_Ollama source code, so
these helper scripts are designed to be copied into the installed app folder:

```text
C:\Program Files\Creolight\AR_Camera_Ollama
```

## Files

- `复制新脚本到项目.bat`
  - Copy helper for machines where `C:\Users\lodge\AR_Camera_Ollama` does not
    yet contain the new root scripts or `tools\windows`.
  - Run it from the downloaded helper bundle. It copies:

    ```text
    build_ar_camera_ollama_installer.bat
    制作安装包.bat
    制作安装包_无需Python检测.bat
    tools\windows\*
    ```

  - Default target:

    ```text
    C:\Users\lodge\AR_Camera_Ollama
    ```

- `下载并安装新脚本.bat`
  - Bootstrap helper for the case where only one script was copied and
    `复制新脚本到项目.bat` reports:

    ```text
    ERROR: Missing source tools folder
    ```

  - Downloads the helper branch zip from GitHub, extracts it under `%TEMP%`, and
    calls `复制新脚本到项目.bat` from the extracted full helper bundle.

- `build_ar_camera_ollama_installer.bat`
  - Builds a copyable installer package on the D drive.
  - Defaults to this repaired source folder:

    ```text
    D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
    ```

  - Defaults to this output package folder:

    ```text
    D:\AR_Camera_Ollama_installer
    ```

  - Also tries to create:

    ```text
    D:\AR_Camera_Ollama_installer.zip
    ```

  - The package contains an `app` payload folder and a root `install.bat`.
  - If `package_install_ar_camera_ollama.bat` is missing from `tools\windows`,
    the builder generates a fallback `install.bat` automatically.
  - Excludes local/non-portable folders such as `python_venv`, `.venv`, `venv`,
    `.git`, and `__pycache__`.
  - Writes a build log to:

    ```text
    %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\build_installer_package.log
    ```

- `package_install_ar_camera_ollama.bat`
  - Template used inside the generated package.
  - Copied into the package as both `install.bat` and
    `install_ar_camera_ollama.bat`.
  - Installs the package payload to:

    ```text
    %LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama
    ```

  - Runs `repair_python_venv.bat` after copying files so each new computer gets
    its own clean virtual environment.
  - Writes an install log to:

    ```text
    %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\package_install.log
    ```

- `sync_fixed_build_to_project.bat`
  - Integrates the repaired app folder back into the current project checkout.
  - Defaults to this repaired source folder:

    ```text
    D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
    ```

  - Defaults to this project folder:

    ```text
    C:\Users\lodge\AR_Camera_Ollama
    ```

  - Copies fixed files into the project with `robocopy /E`, not `/MIR`, so it
    updates and adds files without deleting project-only files.
  - Excludes local/non-portable folders such as `python_venv`, `.venv`, `venv`,
    `.git`, `build`, and `dist`.
  - Copies the launcher/repair/install helpers into the project folder.
  - Runs `repair_python_venv.bat` in the project folder so local development can
    start through the fixed launcher.
  - Writes a sync log to:

    ```text
    %LOCALAPPDATA%\Creolight\AR_Camera_Ollama\sync_fixed_build_to_project.log
    ```

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

### Build a D drive installer package

Use this flow when you want one folder or zip that can be copied to a new
computer and installed there.

If the project root contains `build_ar_camera_ollama_installer.bat`, you can run
that root script directly. It calls the implementation in `tools\windows`.

If the project root contains the Chinese alias `制作安装包.bat`, it is the same
package-build entrypoint and can be double-clicked instead.

If an older local `制作安装包.bat` fails with `Python 3.10+ required` or detects
Anaconda, use the no-portable-venv entrypoint instead:

```text
制作安装包_无需Python检测.bat
```

This package flow does not create `python_venv` while building the package. The
generated `install.bat` recreates `python_venv` on the target computer during
installation.

1. Make sure the repaired copy exists at:

   ```text
   D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
   ```

2. Keep these helper files together in one folder:

   ```text
   build_ar_camera_ollama_installer.bat
   package_install_ar_camera_ollama.bat
   repair_python_venv.bat
   launch_ar_camera_ollama.bat
   README_AR_CAMERA_OLLAMA_VENV_FIX.md
   ```

3. Run:

   ```text
   build_ar_camera_ollama_installer.bat
   ```

4. The generated package will be:

   ```text
   D:\AR_Camera_Ollama_installer
   ```

   If zip creation succeeds, there will also be:

   ```text
   D:\AR_Camera_Ollama_installer.zip
   ```

5. Copy either the whole folder or the zip to the new computer.

6. On the new computer, open the copied package folder and double-click:

   ```text
   install.bat
   ```

The new computer install path defaults to:

```text
%LOCALAPPDATA%\Programs\Creolight\AR_Camera_Ollama
```

To choose a different install folder on the new computer:

```text
install.bat "D:\Apps\AR_Camera_Ollama"
```

The generated package does not carry over `python_venv`; it rebuilds the venv on
the target computer during install.

It is OK for the current project checkout to remain on the C drive:

```text
C:\Users\lodge\AR_Camera_Ollama
```

The D drive paths are only used for the repaired source copy and the generated
installer package:

```text
source: D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
output: D:\AR_Camera_Ollama_installer
```

### Integrate the fixed copy into the current project

Use this flow on the development machine to merge the repaired copy into:

```text
C:\Users\lodge\AR_Camera_Ollama
```

1. Keep these helper files together in one folder:

   ```text
   sync_fixed_build_to_project.bat
   install_fixed_ar_camera_ollama.bat
   repair_python_venv.bat
   launch_ar_camera_ollama.bat
   README_AR_CAMERA_OLLAMA_VENV_FIX.md
   ```

2. Make sure the repaired copy exists at:

   ```text
   D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
   ```

3. Run:

   ```text
   sync_fixed_build_to_project.bat
   ```

   This uses the repaired copy as the source and
   `C:\Users\lodge\AR_Camera_Ollama` as the project target automatically.

4. To choose paths explicitly:

   ```text
   sync_fixed_build_to_project.bat "D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix" "C:\Users\lodge\AR_Camera_Ollama"
   ```

5. After syncing, start the project through:

   ```text
   C:\Users\lodge\AR_Camera_Ollama\launch_ar_camera_ollama.bat
   ```

For future packaging, include these files from the project root in the installer
or release bundle:

```text
repair_python_venv.bat
launch_ar_camera_ollama.bat
install_fixed_ar_camera_ollama.bat
README_AR_CAMERA_OLLAMA_VENV_FIX.md
```

The desktop shortcut should point to `launch_ar_camera_ollama.bat`, with the
"Start in" directory set to the installed app folder.

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
app\main.py
app\app.py
app\run.py
src\main.py
scripts\main.py
scripts\run.py
```

If the app uses a different entry file, edit `launch_ar_camera_ollama.bat` and
set the `ENTRY` value to the correct Python file.

If install succeeds but launch reports "Could not find a known Python entry
file", the app files were copied and the venv was created, but the Python entry
file is in a path the launcher does not recognize yet. The launcher prints the
first Python files found under the install folder to help identify the correct
entry.

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
