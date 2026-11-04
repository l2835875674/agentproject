"""对话循环。TODO: 骨架负责人实现。

职责：
1. 维护多轮上下文（最近 N 轮 + 相关档案片段，不要整份塞进去）
2. 调用 ask_llm
3. 把最终结果转成 blocks，交给 to_view
"""


def run_turn(domain_module, session_id: str, user_input: str) -> dict:
    raise NotImplementedError("core/chat.py 待实现")
