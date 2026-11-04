"""状态读写。每个领域一个子目录，互不干扰。"""
import json
from typing import Optional

from backend.config import STATE_DIR


def _path(domain: str, key: str):
    d = STATE_DIR / domain
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.json"


def load_state(domain: str, key: str) -> Optional[dict]:
    p = _path(domain, key)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_state(domain: str, key: str, value: dict) -> None:
    _path(domain, key).write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
