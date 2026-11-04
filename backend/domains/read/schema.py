"""阅读领域的数据结构。这个文件是「概念卡长什么样」的唯一定义。

改动这里 = 改数据合同，必须同步 data/examples/read_concept_card.json。
"""

STATES = ("unresolved", "shaky", "mastered")

# 六个困惑类型（再认优于回忆：让学习者选，不让他自己组织问题）
CONFUSION_TYPES = {
    "term":         "术语不认识",
    "syntax":       "句子结构绕",
    "logic_jump":   "缺前提，逻辑跳了",
    "background":   "缺背景知识",
    "tone":         "语气/限定拿不准",
    "cant_say":     "我好像懂了但说不出来",
}

# 支架层级
HINT_LEVELS = {
    1: "直接解释",
    2: "给提示/类比，让学习者先想",
    3: "请学习者先自述理解，再诊断补足",
}


def new_concept(term: str, chapter: int) -> dict:
    return {
        "term": term,
        "term_en": "",
        "chapter": chapter,
        "status": "unresolved",
        "learner_explanation": "",
        "hint_level_used": 0,
        "visits": [],
        "last_visit": "",
    }


def new_confusion(span: str, confusion_type: str, chapter: int) -> dict:
    if confusion_type not in CONFUSION_TYPES:
        raise ValueError(f"未知困惑类型: {confusion_type}")
    return {
        "span": span,
        "type": confusion_type,
        "chapter": chapter,
        "hint_level": 0,
        "resolved": False,
        "created_at": "",
    }
