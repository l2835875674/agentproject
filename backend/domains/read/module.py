"""阅读领域。负责人：阅读模块开发者。

只需实现五个函数 + 一个 router，不必关心 core 内部怎么实现。
"""
import json
from dataclasses import replace

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.core import agent, settings, storage
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


def archive_brief(session_id: str) -> str:
    """把学习档案压成几行直接塞进 system，省掉"查询"那一整轮请求。"""
    state = storage.load_state(NAME, session_id) or {}
    concepts = state.get("concepts", [])
    if not concepts:
        return "（还没有任何记录。如果涉及新概念，用 add_concept 建档。）"

    label = {"unresolved": "未解决", "shaky": "半懂", "mastered": "能自释"}
    lines = []
    for c in concepts[:12]:                       # 只带最近的 12 条，避免过长
        line = f"- {c['term']}"
        if c.get("term_en"):
            line += f"（{c['term_en']}）"
        line += f" — {label.get(c['status'], c['status'])}"
        if c.get("learner_explanation"):
            line += f'；他之前的原话：「{c["learner_explanation"][:40]}」'
        lines.append(line)
    if len(concepts) > 12:
        lines.append(f"- ……另有 {len(concepts) - 12} 个概念未列出")
    return "\n".join(lines)


def build_messages(span: str, confusion_type: str | None, chapter_title: str,
                   user_message: str | None, session_id: str = "",
                   system_prompt: str | None = None,
                   followup: bool = False) -> list:
    if confusion_type:
        strategy = prompts.BY_CONFUSION.get(confusion_type, "")
        level = LEVEL_BY_TYPE.get(confusion_type, 2)
        type_line = f"【他卡在哪一类】{strategy}"
    else:
        # 学习者直接打字提问：正常回答，不绕圈子
        level = 2
        type_line = f"【他直接提问】\n{prompts.FREE_QUESTION}"

    # 追问时不重复"诊断任务"，否则模型会重新开场
    if followup:
        type_line = (prompts.FOLLOWUP + "\n\n【最初的卡点，仅供背景】\n" + type_line)

    brief = archive_brief(session_id) if session_id else "（无）"
    base_prompt = (system_prompt or "").strip() or prompts.SYSTEM

    system = f"""{base_prompt}

【当前章节】{chapter_title or "（未标注）"}

【学习者选中的原文】
{span or "（这次没有选中具体段落，他直接提问）"}

{type_line}

【这一轮该用的支架层级】
{prompts.level_instruction(level)}

【学习者档案】（已直接给你，不需要再查询）
{brief}

【可用工具】
add_concept 建档、update_concept_status 请求改状态
（改不改由系统判定，被拒绝就如实告诉学习者）。
困惑记录由系统自动写入，你不需要处理。
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
    span: str = ""
    confusion_type: str | None = None    # 不填 = 学习者直接打字提问
    chapter_title: str = ""
    message: str | None = None
    history: list[dict] | None = None    # 之前的对话，用于多轮追问
    # 前端设置面板可覆盖
    reasoning_effort: str | None = None  # off / low / medium
    system_prompt: str | None = None


def _prepare(inp: "AskIn") -> list:
    followup = bool(inp.history)
    messages = build_messages(inp.span, inp.confusion_type,
                              inp.chapter_title, inp.message,
                              session_id=inp.session_id,
                              system_prompt=inp.system_prompt,
                              followup=followup)
    if followup:
        # 多轮追问：保留当前 system，接上之前的对话，再接本轮提问
        messages = [messages[0]] + inp.history + [messages[-1]]
    return messages


def _auto_record(inp: "AskIn") -> None:
    """困惑记录由代码直接写，不占用模型的一轮工具调用。"""
    if inp.confusion_type and inp.span and not inp.history:
        try:
            read_tools.record_confusion(inp.span, inp.confusion_type, 0,
                                        session_id=inp.session_id)
        except Exception:
            pass


def _cfg(inp: "AskIn"):
    """按前端设置覆盖默认参数；没传就用默认。"""
    base = settings.TAGGED if inp.confusion_type else settings.FREE
    if inp.reasoning_effort in ("off", "low", "medium"):
        return replace(base, reasoning_effort=inp.reasoning_effort)
    return base


@router.get("/settings")
def get_settings():
    """设置面板要用的默认值。"""
    return {
        "system_prompt": prompts.SYSTEM,
        "reasoning_effort": settings.FREE.reasoning_effort,
        "model": settings.FREE.model,
        "options": ["off", "low", "medium"],
    }


@router.post("/ask")
def ask(inp: AskIn):
    """非流式版本（调试用）。"""
    _auto_record(inp)
    return agent.run_turn(inp.session_id, _prepare(inp), domain=NAME, cfg=_cfg(inp))


@router.post("/ask_stream")
def ask_stream(inp: AskIn):
    """流式版本：边想边说，前端逐字显示。"""
    _auto_record(inp)
    cfg = _cfg(inp)
    messages = _prepare(inp)

    def gen():
        try:
            for ev in agent.run_turn_stream(inp.session_id, messages,
                                            domain=NAME, cfg=cfg):
                yield "data: " + json.dumps(ev, ensure_ascii=False) + "\n\n"
        except Exception as e:
            # 任何未预期的异常都要告诉前端，不要静默断流
            yield "data: " + json.dumps(
                {"type": "error", "message": f"{type(e).__name__}: {e}"},
                ensure_ascii=False) + "\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
