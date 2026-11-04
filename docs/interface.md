# 接口契约 v1.0（冻结）

> 这是整个项目的接缝。**冻结后，改动必须全员同意。**
> 任何人不许私自改这里的签名。

---

## 一、领域必须实现的五个函数

每个领域（read / physics）在自己的 `module.py` 中实现，签名必须完全一致。

```python
def identify(text: str) -> bool:
    """这段输入属于本领域吗？用于门户分流。"""

def clarify(ir: dict) -> list[str]:
    """还缺哪些信息。返回问题列表，最多 3 个。
    原则：只问「会改变结果」的，其余给默认值并写进 assumptions。"""

def build_ir(text: str, answers: dict = None) -> dict:
    """把自然语言变成结构化中间表示。
    read    -> 概念卡 / 困惑记录
    physics -> SceneSpec
    注意：LLM 只负责产出这个 JSON，不产出最终答案。"""

def validate(ir: dict) -> dict:
    """确定性校验，不经过 LLM。返回：
    { "status": "green" | "yellow" | "red",
      "issues": [ {"level": "...", "message": "..."} ] }
    read    -> 状态机合法性
    physics -> 单位 / 范围 / 极限 / 能量 / 答案"""

def to_view(ir: dict) -> dict:
    """给前端的展示数据，见第三节。"""
```

每个领域还要暴露：

```python
NAME = "read"          # 唯一标识，用于路由和状态分目录
router = APIRouter(prefix="/api/read")
```

---

## 二、core 提供给领域的（骨架负责人实现）

```python
# backend/core/llm.py
def ask_llm(messages: list[dict], tools: list[dict] = None,
            temperature: float = 0.7) -> str: ...

# backend/core/storage.py
def load_state(domain: str, key: str) -> dict: ...
def save_state(domain: str, key: str, value: dict) -> None: ...

# backend/core/tools.py
def register_tool(name: str, schema: dict, fn) -> None: ...
```

**领域可以用这些，但绝不实现这些。** 反过来，core 不知道任何领域细节。

---

## 三、展示契约：to_view 返回什么

前端**只认 blocks**，不认业务字段。这样两个领域共用同一个渲染函数。

```json
{
  "title": "第 3 章 · 认知负荷",
  "blocks": [
    { "type": "header", "text": "第 3 章 · 认知负荷" },
    { "type": "quote",  "text": "选中原文……" },
    { "type": "chips",  "label": "你觉得哪里卡住了？",
      "items": [{"id": "term", "label": "术语不认识"}] },
    { "type": "buttons","items": [{"id": "try", "label": "我试试"},
                                  {"id": "tell", "label": "直接给我讲"}] },
    { "type": "text",   "text": "这里是一段说明。" },
    { "type": "canvas", "spec": { } }
  ]
}
```

**已定义的 block 类型：**

| type | 用途 | 谁用 |
|---|---|---|
| `header` | 标题 | 两个领域 |
| `text` | 普通段落 | 两个领域 |
| `quote` | 引用原文 | 两个领域 |
| `chips` | 可点选标签（困惑类型） | 阅读 |
| `buttons` | 按钮组 | 两个领域 |
| `steps` | 解题步骤列表 | 物理 |
| `canvas` | 交给渲染器的场景 | 物理 |
| `table` | 参数表 / 假设卡 | 两个领域 |

新增 block 类型 = 一次全员约定，不许单方面加。

---

## 四、状态与存档格式

```
data/state/<domain>/<session_id>.json
```

阅读模块的概念卡示例见 `data/examples/read_concept_card.json`，
物理模块的 SceneSpec 示例见 `data/examples/physics_scene_spec.json`。

**这两个 JSON 是合同本身。** 谁都照它写，谁都别自己发明字段。

---

## 五、变更流程

1. 谁想改接口 → 在组会提出，说清为什么现有的不够
2. 全员同意 → 改本文档版本号（v1.0 → v1.1）
3. **同一天**所有人一起改，不许拖着
