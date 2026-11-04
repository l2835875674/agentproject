# 给 AI 助手的工作须知

> 每次开工，把下面「提示词」整块复制给你的 AI，再告诉它你要做什么。

---

## 提示词（直接复制）

```
你正在协助开发一个教育智能体项目，仓库根目录是 agentproject/。

开工前请先读这四个文件，读完再动手：
  1. README.md              —— 项目约定与分工
  2. docs/interface.md      —— 五个接口的合同（已冻结）
  3. data/examples/*.json   —— 数据结构样例（合同）
  4. 你要改的那个文件夹里的所有文件

【硬性禁止】
- 不许改 docs/interface.md 和 data/examples/ 里的任何内容
- 不许改你负责范围以外的文件夹
- 不许在代码里写死 API key、绝对路径、localhost 地址
- 不许引入新的第三方依赖（先问）
- 不许把状态更新写成"模型输出文本后解析"，必须走工具调用
- 不许删除已有的 TODO 注释而不实现它

【必须遵守】
- 所有配置从 backend/config.py 读，不要自己 os.getenv
- 前端请求一律用相对路径 /api/...，不要写 http://
- 新增的数据字段，必须同时更新 data/examples/ 里的样例
- 中文注释，术语给英文对照
- 一次只改一个文件或一个函数，改完说清楚改了什么

【交付前自检】
- 这段代码跑得起来吗？怎么验证？
- 我改的东西有没有碰到别人的文件夹？
- 有没有破坏 docs/interface.md 里定义的签名？
```

---

## 按角色的补充说明

### 阅读负责人

```
你的范围：backend/domains/read/ 和 frontend/read/
你的重点：prompts.py 里的判断，比代码更重要。
状态机的转移规则已经写好（engine.py），不要改，除非全员同意。
```

### 物理负责人

```
你的范围：backend/domains/physics/ 和 frontend/physics/
你的重点：解析解必须精确，不做数值仿真。
solver.py 和 validator.py 现在是空的，需要你实现。
```

### 骨架负责人

```
你的范围：backend/core/ 和 backend/app.py
你是唯一能改 core/ 的人。
当前 core 还缺：agent 循环、工具执行、记忆、设置、追踪。
先实现 agent.py，其他领域才能跑起来。
```

### 前端 / 门户负责人

```
你的范围：frontend/index.html、theme.css、blocks.js
theme.css 是唯一的设计强约束，改动要全员同意。
blocks.js 里新增 block 类型，必须同步 docs/interface.md。
```

---

## 交付模板

改完之后，在群里这样说：

```
【模块】read / physics / core / frontend
【改了什么】一句话
【改了哪些文件】
【怎么验证】具体命令或点击路径
【有没有用到别人还没做的部分】是/否 + 是什么
【卡在哪】没有就写"无"
```

最后一行最重要。**没写"卡在哪"的，默认没有卡。**
