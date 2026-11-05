"""AI 参数。可按会话覆盖，不要写死在业务代码里。"""
from dataclasses import dataclass

from backend.config import MODEL


@dataclass
class AgentSettings:
    model: str = MODEL
    temperature: float = 0.7
    max_steps: int = 5              # 循环步数上限
    max_seconds: float = 60.0       # 单轮墙钟上限，防止卡死
    reasoning_effort: str | None = "low"   # off / low / medium，越低越快


DEFAULT = AgentSettings()

# 点标签 = 需要判断学习者卡在哪一层，稍微多想想
TAGGED = AgentSettings(reasoning_effort="low")

# 直接打字 = 正常问答，不需要长思考
FREE = AgentSettings(reasoning_effort="off")
