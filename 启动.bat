@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [错误] 还没装依赖。请先在命令行运行: uv sync
  pause
  exit /b 1
)

if not exist ".env" (
  echo [错误] 缺少 .env 文件，请复制 .env.example 为 .env 并填入 API key
  pause
  exit /b 1
)

echo 正在启动服务... 浏览器会自动打开
echo 关闭本窗口即可停止服务
echo.
start "" http://localhost:8000/read/
".venv\Scripts\python.exe" -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
pause
