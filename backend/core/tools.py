"""工具注册与执行。TODO: 骨架负责人实现。

状态机必须通过工具调用落地，不能让模型自由发挥去改档案。
"""

_REGISTRY = {}


def register_tool(name: str, schema: dict, fn) -> None:
    _REGISTRY[name] = {"schema": schema, "fn": fn}


def call(name: str, args: dict):
    if name not in _REGISTRY:
        raise KeyError(f"未注册的工具: {name}")
    return _REGISTRY[name]["fn"](**args)
