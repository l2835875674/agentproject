"""工具注册与执行。

铁律：模型只能"请求"调用工具，改不改由工具内部的代码决定。
"""
from typing import Callable, Dict, List, Optional

_REGISTRY: Dict[str, dict] = {}


def register(name: str, description: str, parameters: dict,
             fn: Callable, domain: Optional[str] = None) -> None:
    _REGISTRY[name] = {
        "domain": domain,
        "schema": {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        },
        "fn": fn,
    }


def schemas(domain: Optional[str] = None) -> List[dict]:
    """给模型看的工具清单。domain 不为空时只返回该领域的（白名单）。"""
    return [v["schema"] for v in _REGISTRY.values()
            if domain is None or v["domain"] == domain]


def call(name: str, args: dict) -> dict:
    """执行工具。任何异常都转成结构化错误回传给模型，不让循环崩掉。"""
    item = _REGISTRY.get(name)
    if item is None:
        return {"ok": False, "error": f"未注册的工具: {name}"}
    try:
        result = item["fn"](**args)
        return {"ok": True, "result": result}
    except TypeError as e:
        return {"ok": False, "error": f"参数不匹配: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def clear() -> None:
    """测试用：清空注册表。"""
    _REGISTRY.clear()


# ---- 会话上下文（工具函数用它知道自己属于哪个会话） ----
import contextvars

_CTX: contextvars.ContextVar[dict] = contextvars.ContextVar("tool_ctx", default={})


def set_context(ctx: dict) -> None:
    _CTX.set(ctx)


def get_context() -> dict:
    return _CTX.get()
