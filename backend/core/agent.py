"""Agent 循环：思考 → 调工具 → 看结果 → 再想，直到不需要工具。

这是整个项目"模型只能提议、不能决定"的落地处。
"""
import json
from typing import List, Optional

from backend.core import llm, settings, tools, trace


def run_turn(session_id: str, messages: List[dict],
             domain: Optional[str] = None,
             cfg: Optional[settings.AgentSettings] = None) -> dict:
    """跑一轮 agent。返回 {"reply": str, "steps": int, "tool_calls": [...]}"""
    cfg = cfg or settings.DEFAULT
    tool_schemas = tools.schemas(domain) or None
    used = []

    # 工具函数靠这个知道自己服务哪个会话
    tools.set_context({"session_id": session_id, "domain": domain})

    for step in range(cfg.max_steps):
        resp = llm.client().chat.completions.create(
            model=cfg.model,
            messages=messages,
            temperature=cfg.temperature,
            tools=tool_schemas,
        )
        msg = resp.choices[0].message

        # 没有工具调用 → 这一轮结束
        if not msg.tool_calls:
            trace.log(session_id, {"step": step, "type": "reply",
                                   "content": msg.content})
            return {"reply": msg.content or "", "steps": step + 1,
                    "tool_calls": used}

        # 把模型的工具请求记回对话
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name,
                              "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })

        # 逐个执行，结果喂回去
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            outcome = tools.call(tc.function.name, args)
            used.append({"name": tc.function.name, "args": args,
                         "ok": outcome.get("ok")})
            trace.log(session_id, {"step": step, "type": "tool_call",
                                   "name": tc.function.name, "args": args,
                                   "ok": outcome.get("ok"),
                                   "outcome": outcome.get("result") or outcome.get("error")})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(outcome, ensure_ascii=False),
            })

    # 达到步数上限
    trace.log(session_id, {"type": "max_steps_reached", "steps": cfg.max_steps})
    return {"reply": "（这一轮调用次数达到上限，先停在这里）",
            "steps": cfg.max_steps, "tool_calls": used}
