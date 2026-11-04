"""每轮的可观测记录。答辩时能现场展示"它想了什么、调了什么工具"。

写入 data/state/traces/<session_id>.jsonl，只追加。
"""
import json
from datetime import datetime

from backend.config import STATE_DIR


def _path(session_id: str):
    d = STATE_DIR / "traces"
    d.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "default"
    return d / f"{safe}.jsonl"


def log(session_id: str, event: dict) -> None:
    event = {"ts": datetime.now().isoformat(timespec="seconds"), **event}
    with _path(session_id).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
