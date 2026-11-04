"""把阅读领域的数据转成前端 block 列表。见 docs/interface.md 第三节。"""
from backend.domains.read import schema


def confusion_chips() -> dict:
    return {
        "type": "chips",
        "label": "你觉得哪里卡住了？",
        "items": [{"id": k, "label": v} for k, v in schema.CONFUSION_TYPES.items()],
    }


def selection_view(span: str, chapter_title: str) -> dict:
    return {
        "title": chapter_title,
        "blocks": [
            {"type": "header", "text": chapter_title},
            {"type": "quote", "text": span},
            confusion_chips(),
        ],
    }


def concept_card_view(concept: dict) -> dict:
    status_text = {
        "unresolved": "未解决",
        "shaky": "半懂",
        "mastered": "能自释",
    }[concept["status"]]
    return {
        "type": "card",
        "title": concept["term"],
        "subtitle": concept.get("term_en", ""),
        "rows": [
            {"k": "状态", "v": status_text},
            {"k": "你的解释", "v": concept.get("learner_explanation") or "（还没有）"},
            {"k": "出现章节", "v": "、".join(concept.get("visits", [])) or "—"},
        ],
        "actions": [{"id": "reexplain", "label": "我重新解释一遍"}],
    }


def session_summary_view(summary: dict) -> dict:
    c = summary["concept_counts"]
    rows = [
        {"k": "能自己解释", "v": f'{c["mastered"]} 个'},
        {"k": "半懂", "v": f'{c["shaky"]} 个'},
        {"k": "未解决", "v": f'{c["unresolved"]} 个'},
        {"k": "支架依赖度", "v": f'{int(summary["hint_dependency"] * 100)}%'},
    ]
    return {
        "title": "本节理解体检",
        "blocks": [
            {"type": "header", "text": "本节理解体检"},
            {"type": "table", "rows": rows},
            {"type": "text", "text": "要不要花 2 分钟，把本节核心概念用自己的话说一遍？"},
            {"type": "buttons", "items": [{"id": "review", "label": "开始复述"}]},
        ],
    }
