"""AI 参数。可按会话覆盖，不要写死在业务代码里。"""
from dataclasses import dataclass

from backend.config import MODEL


@dataclass
class AgentSettings:
    model: str = MODEL
    temperature: float = 0.7
    max_steps: int = 6          # agent 循环上限，防跑飞
    reasoning_effort: str | None = None   # 部分模型支持 low/medium/high


DEFAULT = AgentSettings()
