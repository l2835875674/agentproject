"""阅读领域。负责人：阅读模块开发者。

只需实现五个函数 + 一个 router，不必关心 core 内部怎么实现。
"""
from fastapi import APIRouter
from pydantic import BaseModel

from backend.core import agent, storage
from backend.domains.read import engine, prompts, schema, tools as read_tools
from backend.domains.read import to_view as tv

NAME = "read"
TITLE = "阅读学习伙伴"
router = APIRouter(prefix="/api/read", tags=["read"])

read_tools.register_all()


# ---------------- 五个接口 ----------------

def identify(text: str) -> bool:
    """阅读模块的输入是「选中的段落」，通常较长且包含英文。"""
    return len(text) > 40


def clarify(ir: dict) -> list:
    """阅读模块的澄清就是那六个困惑标签——让学习者选，不让他组织问题。"""
    return []


def build_ir(text: str, answers: dict = None) -> dict:
    """TODO: 调 llm.ask_json 抽出概念和困惑类型。"""
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
    return {"status": "green", "issues": []}


def to_view(ir: dict) -> dict:
    return tv.session_summary_view(engine.summarize(
        ir.get("concepts", []), ir.get("confusions", [])))


# ---------------- 困惑类型 → 支架层级 ----------------

LEVEL_BY_TYPE = {
    "term": 1,
    "syntax": 1,
    "background": 1,
    "tone": 2,
    "logic_jump": 2,
    "cant_say": 3,
}


def build_messages(span: str, confusion_type: str, chapter_title: str,
                   user_message: str | None) -> list:
    strategy = prompts.BY_CONFUSION.get(confusion_type, "")
    level = LEVEL_BY_TYPE.get(confusion_type, 2)

    system = f"""{prompts.SYSTEM}

【当前章节】{chapter_title or "（未标注）"}

【学习者选中的原文】
{span}

【他卡在哪一类】{strategy}

【这一轮该用的支架层级】
{prompts.level_instruction(level)}

【档案工具】
你可以用 get_concept / list_concepts / get_hint_level 查询学习者之前的理解，
用 add_concept / record_confusion 记录这一轮，
用 update_concept_status 请求改变状态——但改不改由系统判定，被拒绝就如实告诉学习者。
"""

    user = user_message or "（学习者刚刚选中了这段文字，还没有说话）"
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


# ---------------- HTTP 接口 ----------------

class SelectIn(BaseModel):
    session_id: str
    span: str
    chapter_title: str = ""


@router.post("/select")
def select(inp: SelectIn):
    return tv.selection_view(inp.span, inp.chapter_title)


class AskIn(BaseModel):
    session_id: str
    span: str
    confusion_type: str
    chapter_title: str = ""
    message: str | None = None


@router.post("/ask")
def ask(inp: AskIn):
    """学习者点了某个困惑标签之后，跑一轮真正的 agent。"""
    messages = build_messages(inp.span, inp.confusion_type,
                              inp.chapter_title, inp.message)
    return agent.run_turn(inp.session_id, messages, domain=NAME)


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
    return {"ok": ok, "status": concept["status"]}


@router.get("/archive/{session_id}")
def archive(session_id: str):
    """学习档案：概念卡 + 理解体检。"""
    state = storage.load_state(NAME, session_id) or {
        "concepts": [], "confusions": [], "profile": {}
    }
    return {
        "concepts": state.get("concepts", []),
        "summary": engine.summarize(state.get("concepts", []),
                                    state.get("confusions", [])),
    }
