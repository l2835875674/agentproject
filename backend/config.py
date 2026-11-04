"""所有配置都从环境变量读。代码里不许写死 key、端口、路径。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("MODEL", "deepseek-flash")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data")).resolve()
STATE_DIR = DATA_DIR / "state"
FRONTEND_DIR = BASE_DIR / "frontend"

STATE_DIR.mkdir(parents=True, exist_ok=True)
