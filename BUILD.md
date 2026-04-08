# HuaShengOCR 打包说明

## 已生成资源

- `assets/huashengocr.png`
- `assets/huashengocr.ico`
- `assets/huashengocr.icns`

## macOS 打包

使用 PyInstaller 生成 `.app`：

```bash
./.venv/bin/pyinstaller --noconfirm --windowed --name HuaShengOCR --icon assets/huashengocr.icns --add-data 'assets:assets' main.py
```

产物目录：

- `dist/HuaShengOCR.app`

## Windows 打包（在 Windows 上执行）

建议在 Windows 机器上运行：

```bat
.venv\Scripts\pyinstaller --noconfirm --windowed --name HuaShengOCR --icon assets\huashengocr.ico --add-data "assets;assets" main.py
```

产物目录：

- `dist\HuaShengOCR\`
- 或 `dist\HuaShengOCR.exe`

## 说明

- `.ico` 用于 Windows
- `.icns` 用于 macOS
- 当前项目已经把应用标题和品牌文案统一为 HuaShengOCR
