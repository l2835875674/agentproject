"""Agent 循环：思考 → 调工具 → 看结果 → 再想，直到不需要工具。

这是整个项目"模型只能提议、不能决定"的落地处。
"""
import json
import time
from typing import List, Optional

from backend.core import llm, settings, tools, trace

# 预算用尽时的强制收尾提示：不给工具，逼模型给结论
FORCE_FINISH = {
    "role": "user",
    "content": "（系统提示：这一轮的工具调用已经结束。"
               "请基于目前掌握的信息，直接用中文给出回答，不要再调用任何工具。）",
}


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
            **llm.build_kwargs(messages, tools=tool_schemas, cfg=cfg)
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


# ---------------- 流式版本 ----------------

def run_turn_stream(session_id: str, messages: List[dict],
                    domain: Optional[str] = None,
                    cfg: Optional[settings.AgentSettings] = None):
    """逐段产出事件，供 SSE 推给前端。

    事件类型：
      {"type": "status", "text": "..."}   进度提示
      {"type": "delta",  "text": "..."}   正文增量
      {"type": "tool",   "name": "..."}   调用了某工具
      {"type": "done"}                    结束
    """
    cfg = cfg or settings.DEFAULT
    tool_schemas = tools.schemas(domain) or None
    tools.set_context({"session_id": session_id, "domain": domain})
    t0 = time.time()

    for step in range(cfg.max_steps):
        # 时间预算用尽 → 强制收尾
        if time.time() - t0 > cfg.max_seconds:
            yield {"type": "status", "text": "时间到，正在收尾…"}
            yield from _force_finish(session_id, messages, cfg)
            return
        stream = llm.client().chat.completions.create(
            **llm.build_kwargs(messages, tools=tool_schemas, cfg=cfg, stream=True)
        )

        content_parts: List[str] = []
        calls: dict = {}
        said_thinking = False

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if getattr(delta, "reasoning_content", None) and not said_thinking:
                said_thinking = True
                yield {"type": "status", "text": "思考中…"}

            if delta.content:
                content_parts.append(delta.content)
                yield {"type": "delta", "text": delta.content}

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    slot = calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            slot["name"] += tc.function.name
                        if tc.function.arguments:
                            slot["arguments"] += tc.function.arguments

        # 没有工具调用 → 这一轮结束
        if not calls:
            trace.log(session_id, {"step": step, "type": "reply",
                                   "content": "".join(content_parts)})
            yield {"type": "done"}
            return

        # 有工具调用：把请求记回对话，执行后继续
        messages.append({
            "role": "assistant",
            "content": "".join(content_parts),
            "tool_calls": [
                {"id": v["id"], "type": "function",
                 "function": {"name": v["name"], "arguments": v["arguments"]}}
                for v in calls.values()
            ],
        })

        for v in calls.values():
            try:
                args = json.loads(v["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            outcome = tools.call(v["name"], args)
            trace.log(session_id, {"step": step, "type": "tool_call",
                                   "name": v["name"], "args": args,
                                   "ok": outcome.get("ok")})
            yield {"type": "tool", "name": v["name"], "ok": outcome.get("ok")}
            messages.append({
                "role": "tool",
                "tool_call_id": v["id"],
                "content": json.dumps(outcome, ensure_ascii=False),
            })

    # 步数用尽 → 不给工具，逼模型给结论
    yield {"type": "status", "text": "步数用尽，正在收尾…"}
    yield from _force_finish(session_id, messages, cfg)


def _force_finish(session_id: str, messages: List[dict],
                  cfg: settings.AgentSettings):
    """预算用尽时的兜底：不带任何工具再问一次，强制输出结论。"""
    try:
        stream = llm.client().chat.completions.create(
            **llm.build_kwargs(messages + [FORCE_FINISH], tools=None, cfg=cfg, stream=True)
        )
        parts: List[str] = []
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                parts.append(delta.content)
                yield {"type": "delta", "text": delta.content}
        trace.log(session_id, {"type": "forced_finish", "content": "".join(parts)})
    except Exception as e:
        yield {"type": "delta", "text": f"（收尾失败：{e}）"}
        trace.log(session_id, {"type": "forced_finish_error", "error": str(e)})
    yield {"type": "done"}
