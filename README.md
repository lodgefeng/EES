# E-elements

## Windows AR_Camera_Ollama install helpers

Windows helper scripts for the AR_Camera_Ollama `python_venv` launch issue are
available under:

```text
tools/windows
```

To integrate the repaired copy back into the current project checkout:

```text
tools/windows/sync_fixed_build_to_project.bat
```

The sync script defaults to:

```text
fixed source: D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
project dir:  C:\Users\lodge\AR_Camera_Ollama
```

To build a copyable installer package on the D drive:

```text
tools/windows/build_ar_camera_ollama_installer.bat
```

The package output defaults to:

```text
D:\AR_Camera_Ollama_installer
D:\AR_Camera_Ollama_installer.zip
```

For new computers, use:

```text
tools/windows/install_fixed_ar_camera_ollama.bat
```

The installer defaults to the fixed source folder:

```text
D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
```