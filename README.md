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

For new computers, use:

```text
tools/windows/install_fixed_ar_camera_ollama.bat
```

The installer defaults to the fixed source folder:

```text
D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix
```