"""阅读领域的确定性引擎：概念状态机。

铁律：状态只能由代码改，不能让 LLM 直接写。
LLM 想改状态，只能调用 transition()，非法转移会被拒绝。
"""

ALLOWED = {
    "unresolved": {"shaky"},
    "shaky": {"mastered", "unresolved"},
    "mastered": {"shaky"},
}

# 升级到 mastered 的门槛：自述质量分 + 本轮是否依赖提示
SELF_EXPLAIN_THRESHOLD = 0.6


def transition(current: str, target: str, self_explain_score: float,
               used_hint: bool) -> bool:
    """尝试状态转移。合法且满足证据要求才返回 True。

    参数
    ----
    current: 当前状态
    target:  目标状态
    self_explain_score: 这一轮学习者自述的质量 0~1（由模型打分，人工可复核）
    used_hint: 这一轮是否用了提示

    规则
    ----
    1. 只允许 ALLOWED 里列出的转移
    2. 升到 mastered 必须：自述达标 且 不依赖提示
    3. 降级（mastered -> shaky）不需要证据，复测失败即可
    """
    if target not in ALLOWED.get(current, set()):
        return False

    if target == "mastered":
        return self_explain_score >= SELF_EXPLAIN_THRESHOLD and not used_hint

    return True


def next_default_level(concept: dict) -> int:
    """根据这条概念的既往表现，决定默认给几层支架。

    提示依赖越高，越该多给支撑；已经能自释的，应该开始撤除。
    """
    status = concept.get("status", "unresolved")
    if status == "mastered":
        return 2          # 开始撤支架
    if status == "shaky":
        return 3          # 请他自己先说
    return 1              # 全新概念，直接解释


def summarize(concepts: list, confusions: list) -> dict:
    """会话结束时的「理解体检」数据。"""
    counts = {"mastered": 0, "shaky": 0, "unresolved": 0}
    for c in concepts:
        counts[c.get("status", "unresolved")] = counts.get(c.get("status", "unresolved"), 0) + 1

    by_type = {}
    for f in confusions:
        by_type[f["type"]] = by_type.get(f["type"], 0) + 1

    # 支架依赖度 = 用过提示的困惑 / 全部困惑
    total = len(confusions)
    dependent = sum(1 for f in confusions if f.get("hint_level", 0) > 0)
    return {
        "concept_counts": counts,
        "confusion_by_type": by_type,
        "hint_dependency": round(dependent / total, 2) if total else 0.0,
    }
