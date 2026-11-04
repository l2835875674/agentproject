"""阅读领域暴露给模型的工具。

★ 关键设计：模型只能"请求"改状态，改不改由 engine.transition() 决定。
"""
from backend.core import storage, tools
from backend.domains.read import engine

NAME = "read"


def _sid() -> str:
    return tools.get_context().get("session_id", "default")


def _load() -> dict:
    return storage.load_state(NAME, _sid()) or {
        "book": "", "concepts": [], "confusions": [], "profile": {}
    }


def _save(state: dict) -> None:
    storage.save_state(NAME, _sid(), state)


# ---------------- 工具实现 ----------------

def update_concept_status(term: str, target: str,
                          self_explain_score: float = 0.0,
                          used_hint: bool = False) -> dict:
    """模型请求改变某个概念的状态。非法转移会被代码拒绝。"""
    state = _load()
    concept = next((c for c in state["concepts"] if c["term"] == term), None)
    if concept is None:
        return {"ok": False, "reason": f"概念「{term}」不在档案里，请先调用 add_concept"}

    ok = engine.transition(concept["status"], target,
                           self_explain_score, used_hint)
    if ok:
        concept["status"] = target
        concept["hint_level_used"] = 3 if used_hint else concept.get("hint_level_used", 0)
        _save(state)
        return {"ok": True, "status": target}
    return {"ok": False, "status": concept["status"],
            "reason": "非法转移或证据不足：升到 mastered 需要自述达标且本轮未用提示"}


def add_concept(term: str, term_en: str = "", chapter: int = 0) -> dict:
    state = _load()
    if any(c["term"] == term for c in state["concepts"]):
        return {"ok": False, "reason": "已存在"}
    state["concepts"].append({
        "term": term, "term_en": term_en, "chapter": chapter,
        "status": "unresolved", "learner_explanation": "",
        "hint_level_used": 0, "visits": [], "last_visit": "",
    })
    _save(state)
    return {"ok": True, "term": term}


def record_confusion(span: str, confusion_type: str, chapter: int = 0) -> dict:
    from backend.domains.read import schema
    if confusion_type not in schema.CONFUSION_TYPES:
        return {"ok": False, "reason": f"未知困惑类型: {confusion_type}"}
    state = _load()
    state["confusions"].append(schema.new_confusion(span, confusion_type, chapter))
    _save(state)
    return {"ok": True}


def get_concept(term: str) -> dict:
    state = _load()
    concept = next((c for c in state["concepts"] if c["term"] == term), None)
    return concept or {"found": False}


def list_concepts() -> dict:
    return {"concepts": [{"term": c["term"], "status": c["status"]}
                         for c in _load()["concepts"]]}


def get_hint_level(term: str) -> dict:
    """该给几层支架。由代码算，不让模型自己拍。"""
    concept = get_concept(term)
    if not concept or concept.get("found") is False:
        return {"level": 1, "reason": "新概念"}
    return {"level": engine.next_default_level(concept), "reason": concept["status"]}


# ---------------- 注册 ----------------

def register_all() -> None:
    tools.register(
        "update_concept_status",
        "请求改变某个概念的学习状态。target 只能是 unresolved / shaky / mastered。"
        "升到 mastered 必须提供自述质量分且本轮未用提示，否则会被拒绝。",
        {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "概念词条"},
                "target": {"type": "string", "enum": ["unresolved", "shaky", "mastered"]},
                "self_explain_score": {"type": "number", "description": "学习者自述质量 0~1"},
                "used_hint": {"type": "boolean", "description": "本轮是否用了提示"},
            },
            "required": ["term", "target"],
        },
        update_concept_status, domain=NAME,
    )
    tools.register(
        "add_concept", "把新概念加进学习档案。",
        {"type": "object",
         "properties": {"term": {"type": "string"},
                        "term_en": {"type": "string"},
                        "chapter": {"type": "integer"}},
         "required": ["term"]},
        add_concept, domain=NAME,
    )
    tools.register(
        "record_confusion", "记录一次困惑。type 必须是六种之一。",
        {"type": "object",
         "properties": {"span": {"type": "string"},
                        "confusion_type": {"type": "string",
                                           "enum": ["term", "syntax", "logic_jump",
                                                    "background", "tone", "cant_say"]},
                        "chapter": {"type": "integer"}},
         "required": ["span", "confusion_type"]},
        record_confusion, domain=NAME,
    )
    tools.register(
        "get_concept", "查某个概念在档案里的状态和学习者之前的原话解释。",
        {"type": "object", "properties": {"term": {"type": "string"}},
         "required": ["term"]},
        get_concept, domain=NAME,
    )
    tools.register(
        "list_concepts", "列出档案里所有概念及其状态。",
        {"type": "object", "properties": {}},
        list_concepts, domain=NAME,
    )
    tools.register(
        "get_hint_level", "查询该给几层支架（1 直讲 / 2 给提示 / 3 先自述）。由系统决定，不要自己猜。",
        {"type": "object", "properties": {"term": {"type": "string"}},
         "required": ["term"]},
        get_hint_level, domain=NAME,
    )
