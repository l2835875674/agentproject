"""物理领域。负责人：物理模块开发者。

只需实现五个函数 + 一个 router。
"""
from fastapi import APIRouter

from backend.domains.physics import schema

NAME = "physics"
TITLE = "物理讲题编译器"
router = APIRouter(prefix="/api/physics", tags=["physics"])


def identify(text: str) -> bool:
    keywords = ("斜面", "传送带", "物块", "摩擦", "倾角")
    return sum(k in text for k in keywords) >= 2


def clarify(ir: dict) -> list:
    """TODO: 只问会改变结果的参数，最多 3 个。"""
    return []


def build_ir(text: str, answers: dict = None) -> dict:
    """TODO: 调 llm.ask_json 生成 SceneSpec。"""
    return {"model": "incline_conveyor"}


def validate(ir: dict) -> dict:
    """TODO: 解析解 + 单位/范围/极限/能量校验。"""
    ok, msg = schema.is_valid(ir)
    if not ok:
        return {"status": "red", "issues": [{"level": "red", "message": msg}]}
    return {"status": "yellow", "issues": [{"level": "yellow", "message": "解析解尚未接入"}]}


def to_view(ir: dict) -> dict:
    """TODO: 步骤面板 + v-t 图 + canvas。"""
    return {"title": "物理讲题", "blocks": [
        {"type": "header", "text": "物理讲题编译器"},
        {"type": "text", "text": "渲染器待接入。"},
    ]}


@router.get("/models")
def models():
    return [{"id": "incline_conveyor", "title": "斜面 + 水平传送带"}]
