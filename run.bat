@echo off
setlocal
cd /d %~dp0

where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_BIN=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PYTHON_BIN=py
    ) else (
        echo 未找到 Python，请先安装 Python 3.10+
        pause
        exit /b 1
    )
)

if not exist .venv (
    echo [1/3] 创建虚拟环境...
    %PYTHON_BIN% -m venv .venv
)

call .venv\Scripts\activate.bat

echo [2/3] 安装/更新依赖...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [3/3] 启动本地 OCR GUI...
python main.py

endlocal
