"""阅读领域。负责人：阅读模块开发者。

只需实现五个函数 + 一个 router，不必关心 core 内部怎么实现。
"""
from fastapi import APIRouter
from pydantic import BaseModel

from backend.core import llm, storage
from backend.domains.read import engine, schema
from backend.domains.read import to_view as tv

NAME = "read"
TITLE = "阅读学习伙伴"
router = APIRouter(prefix="/api/read", tags=["read"])


# ---------------- 五个接口 ----------------

def identify(text: str) -> bool:
    """阅读模块的输入是「选中的段落」，通常较长且包含英文。
    这里先给一个最简单的判据，之后可换成模型判断。
    """
    return len(text) > 40


def clarify(ir: dict) -> list:
    """阅读模块的澄清就是那六个困惑标签——让学习者选，不让他组织问题。"""
    return []


def build_ir(text: str, answers: dict = None) -> dict:
    """TODO: 调 llm.ask_json 抽出概念和困惑类型。
    现在返回一个最小可用结构。
    """
    chapter = (answers or {}).get("chapter", 0)
    return {
        "book": (answers or {}).get("book", ""),
        "concepts": [],
        "confusions": [],
        "chapter": chapter,
    }


def validate(ir: dict) -> dict:
    """阅读领域的校验 = 状态机合法性 + 数据完整性。不经过 LLM。"""
    issues = []
    for c in ir.get("concepts", []):
        if c.get("status") not in schema.STATES:
            issues.append({"level": "red",
                           "message": f'概念 {c.get("term")} 的状态非法：{c.get("status")}'})
    if issues:
        return {"status": "red", "issues": issues}
    has_assumption = bool(ir.get("assumptions"))
    return {"status": "yellow" if has_assumption else "green", "issues": []}


def to_view(ir: dict) -> dict:
    return tv.session_summary_view(engine.summarize(
        ir.get("concepts", []), ir.get("confusions", [])))


# ---------------- HTTP 接口 ----------------

class SelectIn(BaseModel):
    session_id: str
    span: str
    chapter_title: str = ""


@router.post("/select")
def select(inp: SelectIn):
    return tv.selection_view(inp.span, inp.chapter_title)


class TransitionIn(BaseModel):
    session_id: str
    term: str
    target: str
    self_explain_score: float = 0.0
    used_hint: bool = False


@router.post("/transition")
def transition(inp: TransitionIn):
    state = storage.load_state(NAME, inp.session_id) or {"concepts": [], "confusions": []}
    concept = next((c for c in state["concepts"] if c["term"] == inp.term), None)
    if concept is None:
        return {"ok": False, "reason": "概念不存在"}

    ok = engine.transition(concept["status"], inp.target,
                           inp.self_explain_score, inp.used_hint)
    if ok:
        concept["status"] = inp.target
        storage.save_state(NAME, inp.session_id, state)
    return {"ok": ok, "status": concept["status"] if ok else concept["status"]}
