# HuaShengOCR

HuaShengOCR 是一个**纯本地运行**的 Python OCR 桌面工具，使用 **PySide6 GUI**。

## 功能

- 本地桌面 GUI 界面
- 选择图片后直接 OCR 识别
- 显示完整识别文本
- 显示每条识别明细、置信度、坐标框
- 自动检测识别结果里是否包含链接
- 单独提供**人工审核区**
- 展示：
  - 命中多少处文本块
  - 一共识别到多少个链接
  - 哪些文本块命中了链接
  - 具体链接清单
- **命中的文本块红色高亮展示**
- **人工审核结论按钮**：
  - 审核通过
  - 审核拒绝
  - 待复核
- 支持图片格式：png / jpg / jpeg / webp / bmp

## 启动方式

### Windows

双击运行：

```bat
run.bat
```

### macOS / Linux

第一次先给执行权限：

```bash
chmod +x run.sh
```

然后运行：

```bash
./run.sh
```

## 启动脚本会自动做什么

- 自动创建 `.venv` 虚拟环境（如果不存在）
- 自动安装 `requirements.txt` 依赖
- 自动启动 HuaShengOCR 桌面窗口

## 手动启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Windows:

```bat
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

## 项目结构

- `main.py`：主入口
- `app_gui.py`：PySide6 桌面 GUI
- `ocr_core.py`：OCR 核心逻辑
- `link_detector.py`：链接检测
- `run.bat`：Windows 启动脚本
- `run.sh`：macOS / Linux 启动脚本

## 说明

- 当前是**本地桌面版**，不再以 FastAPI 网页服务为主要入口
- OCR 引擎仍然使用项目内置的 OnnxOCR 模型
- 首次启动会稍慢，因为需要安装依赖并首次加载模型
- 如果是第一次运行，建议直接执行 `run.sh` / `run.bat`，不要跳过依赖安装步骤
