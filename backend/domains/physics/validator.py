"""物理可实现性校验。负责人：物理负责人。

TODO: 四类校验，任一项不通过就返回 red/yellow：
1. 单位一致
2. 参数范围合理（倾角 0~60、摩擦系数 0~1、长度 > 0）
3. 约束（传送带太短却要求先加速后匀速 → 矛盾）
4. 能量守恒（重力势能减少 = 末动能 + 热量 + 传送带获得）

这一层是相对 AI 视频的真正壁垒：它不说"做不了动画"，它说"物理上不成立"。
"""


def check(spec: dict) -> dict:
    raise NotImplementedError("physics/validator.py 待实现")
