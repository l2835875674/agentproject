"""物理领域的数据结构：SceneSpec。

样例见 data/examples/physics_scene_spec.json——那是合同。
改动这里必须同步样例文件。
"""

REQUIRED_FIELDS = ("model", "block", "incline", "conveyor", "environment")


def is_valid(spec: dict) -> tuple:
    missing = [f for f in REQUIRED_FIELDS if f not in spec]
    if missing:
        return False, f"缺少字段: {missing}"
    if spec.get("model") != "incline_conveyor":
        return False, "只支持 incline_conveyor 模型"
    return True, ""
