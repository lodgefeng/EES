# AI实验判断功能接入说明

第一版功能已经做成独立 PySide6 页面模块：

```text
feature\ai_experiment_judgement\app\ai_experiment_judgement.py
```

## 功能内容

- 摄像头实时预览。
- 加载标准摆放照片。
- 拍摄当前画面作为标准照片。
- `+ / -` 缩放标准图叠加层。
- `↑ ↓ ← →` 移动标准图叠加层。
- 保存校准参数。
- 点击“拍照判断”，对当前摄像头画面和标准图叠加区域做相似度判断。

这一版使用 OpenCV 做固定机位下的标准图对比，适合先验证流程。后续如果要做器材级判断，再训练 YOLO 检测各个实验器材的位置、角度和缺失状态。

## 复制到当前项目

在下载好的 helper 包根目录运行：

```text
安装AI实验判断功能.bat
```

默认复制到：

```text
C:\Users\lodge\AR_Camera_Ollama\app\ai_experiment_judgement.py
D:\AR_Camera_Ollama_fix\AR_Camera_Ollama_fix\app\ai_experiment_judgement.py
```

同时会复制独立启动脚本：

```text
launch_ai_experiment_judgement.bat
```

运行 `下载并安装新脚本.bat` 或 `复制新脚本到项目.bat` 时，也会自动把该模块复制到本机项目和 D 盘修复源目录。

## 单独测试

在项目根目录运行：

```text
launch_ai_experiment_judgement.bat
```

如果是在安装后的新电脑上测试，则在安装目录运行同名脚本。

## 首页按钮接入

运行下面脚本，会自动：

1. 复制 `ai_experiment_judgement.py`、`home_menu_patch.py`、`launcher_entry.py`
2. 更新 `launch_ar_camera_ollama.bat`，让桌面快捷方式启动时自动插入按钮 05
3. 修复 `app\main.py` 里可能损坏的源码补丁（按钮 05 走运行时注入，不再改 main.py）

```text
安装首页05按钮.bat
```

如果已经安装过，只是桌面打开看不到按钮 05，直接运行：

```text
修复首页05按钮.bat
```

如果桌面快捷方式目标是：

```text
C:\Program Files\Creolight\AR_Camera_Ollama\start_app.bat
```

请运行（推荐，纯英文文件名，避免 cmd 编码错误）：

```text
fix_program_files_button_05.bat
```

双击即可，会自动请求管理员权限，并从 GitHub 下载补丁文件写入 Program Files。

中文文件名包装脚本（效果相同）：

```text
直接从GitHub修复ProgramFiles首页05按钮.bat
```

如果本地已有 helper 包，也可以运行：

```text
修复Creolight安装首页05按钮.bat
```

也可以先更新 helper，再运行：

```text
下载并安装新脚本.bat
修复首页05按钮.bat
```

补丁完成后，重新启动主程序，首页就会出现第 5 个按钮。

如果仍看不到，确认这两个文件存在：

```text
C:\Program Files\Creolight\AR_Camera_Ollama\app\home_menu_patch.py
C:\Program Files\Creolight\AR_Camera_Ollama\app\launcher_entry.py
C:\Program Files\Creolight\AR_Camera_Ollama\start_app.bat
```

并检查日志：

```text
%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\launcher.log
%LOCALAPPDATA%\Creolight\AR_Camera_Ollama\home_menu_patch.log
```

如果 `launcher.log` 里有 `Using launcher entry with home-menu patch.`，说明桌面快捷方式已经走补丁启动链。

如果启动报 `IndentationError` 在 `app\main.py`，运行：

```text
repair_main_py_button05.bat
```

这会移除损坏的源码补丁。按钮 05 仍通过 `launcher_entry` 运行时注入，不需要改 `main.py`。

## 手动接入（备用）

```python
from app.ai_experiment_judgement import AIExperimentJudgementWindow


def open_ai_experiment_judgement(self):
    self.ai_experiment_judgement_window = AIExperimentJudgementWindow()
    self.ai_experiment_judgement_window.resize(1120, 820)
    self.ai_experiment_judgement_window.show()


# 创建首页按钮后：
self.ai_experiment_button.clicked.connect(self.open_ai_experiment_judgement)
```

如果首页原来是用 `QStackedWidget` 切换页面，也可以把 widget 加到 stack：

```python
from app.ai_experiment_judgement import AIExperimentJudgementWidget

self.ai_experiment_page = AIExperimentJudgementWidget()
self.stack.addWidget(self.ai_experiment_page)
self.ai_experiment_button.clicked.connect(
    lambda: self.stack.setCurrentWidget(self.ai_experiment_page)
)
```

## 后续 YOLO 升级建议

第一版是标准图相似度判断。后续如果要精确判断每个模块是否摆放正确，建议：

1. 固定摄像头和实验台。
2. 标注每类实验器材：
   - 激光器
   - 反射镜
   - 分光镜
   - 透镜
   - 白屏
   - 支架
3. 用 YOLO 训练检测框。
4. 保存标准摆放时每个器材的中心点、角度和允许误差。
5. 学生摆放时检测当前器材位置，与标准位置逐项比较。

大模型可以作为中文反馈辅助，不建议作为第一层几何位置判定。
