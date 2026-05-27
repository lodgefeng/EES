# E-elements

## Windows AR_Camera_Ollama install helpers

Windows helper scripts for the AR_Camera_Ollama `python_venv` launch issue are
available under:

```text
tools/windows
```

If the Windows project folder does not have these new scripts yet, run this from
the downloaded helper bundle:

```text
复制新脚本到项目.bat
```

If you only copied that one file and it reports missing `tools\windows`, use the
bootstrap downloader instead:

```text
下载并安装新脚本.bat
```

It copies the root entrypoints and `tools\windows` helpers into:

```text
C:\Users\lodge\AR_Camera_Ollama
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
制作安装包_无需Python检测.bat
```

This is the recommended entrypoint if an older local package script fails with
`Python 3.10+ required` or detects Anaconda.

You can also use:

```text
制作安装包.bat
```

or:

```text
build_ar_camera_ollama_installer.bat
```

This root script calls the implementation under:

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