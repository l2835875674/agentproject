"""阅读状态机的回归测试。改 engine.py 后必须跑这个。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.domains.read import engine


def test_normal_upgrade():
    assert engine.transition("unresolved", "shaky", 0.0, True) is True


def test_cannot_skip_to_mastered():
    # 不允许 unresolved -> mastered 跳级
    assert engine.transition("unresolved", "mastered", 1.0, False) is False


def test_mastered_requires_explanation():
    # 自述不达标不能升
    assert engine.transition("shaky", "mastered", 0.3, False) is False


def test_mastered_requires_no_hint():
    # 靠提示答对的，不算掌握
    assert engine.transition("shaky", "mastered", 0.9, True) is False


def test_mastered_ok():
    assert engine.transition("shaky", "mastered", 0.8, False) is True


def test_downgrade_allowed():
    assert engine.transition("mastered", "shaky", 0.0, False) is True


def test_level_fading():
    assert engine.next_default_level({"status": "unresolved"}) == 1
    assert engine.next_default_level({"status": "shaky"}) == 3
    assert engine.next_default_level({"status": "mastered"}) == 2


if __name__ == "__main__":
    import traceback
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                failed += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print("failed:", failed)
