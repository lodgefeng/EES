# AI实验判断 / AR成像调节 功能说明

## 首页按钮

| 按钮 | 名称 | 功能 |
|------|------|------|
| 05 | AR成像调节 | 摄像头叠图校准、标准图同步预览、4020投放 |
| 06 | AI实验判断 | Ollama 大模型对比实时图与标准图，圈出差异并说明 |

## 05 AR成像调节

- 左侧：摄像头 + 标准图 AR 叠图预览
- 右侧：标准图同步预览（只显示采样/校准后的标准图效果）
- **返回主目录**：回到首页
- **4020投放**：弹出投放控制窗口，把右侧标准图预览投到 JBD4020 控制板
- `+/-`、方向键：调节叠图位置和大小
- 与旧版共用校准文件：`ai_experiment_judgement_calibration.json`

## 06 AI实验判断

- 读取 05 中保存的标准图和校准参数
- 点击 **AI判断差异**：
  1. 用 OpenCV 找出实时画面与标准图的差异区域
  2. 在实时画面上用编号圆圈标出差异
  3. 调用本机 Ollama 视觉模型（默认 `llava`）生成中文说明
- 需要本机已启动 Ollama，并安装视觉模型

## 安装到 Program Files

```text
fix_program_files_button_05.bat
```

或：

```text
安装AI实验判断功能.bat "C:\Program Files\Creolight\AR_Camera_Ollama"
```

会复制 `feature\ai_experiment_judgement\app\` 下全部 `.py` 文件。

## 模块文件

```text
app\experiment_shared.py
app\ar_imaging_adjustment.py
app\ai_experiment_llm_judgement.py
app\jbd4020_cast_support.py
app\home_menu_patch.py
app\launcher_entry.py
app\ai_experiment_judgement.py
```

## 4020 投放说明

投放对话框会自动尝试调用安装目录里已有的：

```text
app\jbd4020_service.py
```

如果该模块存在，即可连接板卡并推送右侧标准图预览帧。

## Ollama 配置

在 06 页面可修改：

- 模型名：默认 `qwen3-vl:2b`（启动时会自动从 Ollama 检测已安装的 vl 模型）
- 地址：默认 `http://127.0.0.1:11434`
- 调用顺序：`/api/chat`（qwen-vl 推荐）→ `/api/generate`（兼容 llava）

如果项目里已有 `app\ollama_vl.py`，后续版本可继续对接该模块。
