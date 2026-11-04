"""领域注册表。core 只认这五个函数，不知道任何领域细节。"""
from typing import Any, Dict

_REQUIRED = ("NAME", "router", "identify", "clarify", "build_ir", "validate", "to_view")
_DOMAINS: Dict[str, Any] = {}


def register(module) -> None:
    missing = [name for name in _REQUIRED if not hasattr(module, name)]
    if missing:
        raise TypeError(f"领域 {module.__name__} 缺少接口: {missing}")
    _DOMAINS[module.NAME] = module


def get(name: str):
    return _DOMAINS.get(name)


def all_domains() -> Dict[str, Any]:
    return dict(_DOMAINS)


def detect(text: str) -> str:
    """猜这段输入属于哪个领域，用于门户分流。"""
    for name, module in _DOMAINS.items():
        try:
            if module.identify(text):
                return name
        except Exception:
            continue
    return "read"
