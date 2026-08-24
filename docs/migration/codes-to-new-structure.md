# 实验代码迁移表

本文档是“全部实验功能”迁移的验收清单。迁移不等于复制脚本：正式模块必须去除
全局可变状态、导入即执行、硬编码路径和 UI/业务耦合。

## 1. Agent loop 实验

| 实验能力 | 正式位置 | 状态/计划 |
| --- | --- | --- |
| native tool schema 与调用转换 | `integrations/models/ollama/client.py` | 已迁移 |
| 工具注册和参数类型转换 | `emc_core.tools` | 已迁移 |
| model → tool → model 循环 | `emc_runtime_local` | 已迁移 |
| `search_cases` 工具 | `emc_core.tools.search_cases` | 已迁移 |
| Prompt JSON 工具协议解析 | `emc_runtime_local` 兼容适配器 | 阶段 4；非默认 |
| 最大迭代、未知工具、工具异常 | runtime + executor | 已迁移，继续补 API 测试 |

来源：

- `experiments/agent-loop/native-tool/*`
- `experiments/agent-loop/prompt-tool/*`
- `docs/research/1-agent-tool-calling.md`

## 2. RAG 与搜索实验

| 实验能力 | 正式位置 | 阶段 |
| --- | --- | --- |
| Ollama 文本嵌入 | `integrations/models/ollama/embeddings.py` | 已迁移 |
| Chroma 惰性连接与余弦检索 | `integrations/vector_stores/chroma/store.py` | 已迁移 |
| 发布数据校验、去重、字段标准化 | `emc_core` repository + `scripts/data` | 3 |
| 可重复构建向量索引（upsert/rebuild） | `scripts/data/build_vector_index.py` | 3 |
| 关键词/指定字段搜索 | `emc_core.application.search_service` | 3 |
| Ollama 不可用时降级关键词搜索 | backend composition/search service | 3 |
| 结构化结果与 Excel 导出 | backend API + desktop save dialog | 3/5 |

来源：

- `experiments/rag/embedding_test.py`
- `experiments/desktop/pyqt6_app/EMC_Fault_Database_Test.py`
- `emc_core.retrieval.json_search`

## 3. Ollama 实验

| 实验能力 | 正式位置 | 阶段 |
| --- | --- | --- |
| `/api/tags` 服务探测 | `integrations/models/ollama/health.py` | 已迁移 |
| 必要时后台启动 `ollama serve` | 同上，由 composition 调用 | 已迁移，阶段 2 接入 |
| 只关闭应用自己启动的进程 | backend lifespan | 2 |
| model/embedding model 配置 | backend settings | 2 |
| 流式 content/thinking 分流 | Ollama adapter + runtime events | 4 |
| 模型缺失与服务不可用诊断 | health/models API | 2 |

来源：`experiments/ollama/*`。实验中的 `ollama run` 启动方式不迁移，因为它是
交互式模型会话，不是服务进程。

## 4. Memory 实验

| 实验能力 | 正式位置 | 阶段 |
| --- | --- | --- |
| 新建、列出、恢复会话 | `session_service` + JSONL store | 4 |
| 首问标题、轮数、更新时间 | session summary | 4 |
| 用户消息先落盘 | chat service | 4 |
| context、hit IDs、thinking、工具轨迹 | session event records | 4 |
| 损坏 JSONL 行容错 | JSONL store | 4 |
| 历史消息重建 | chat service | 4 |
| thinking 保存但不回放 | chat service | 4 |

来源：`experiments/memory/multi_turn.py` 和 `persistent_session.py`。

## 5. PyQt6 桌面实验

| 实验能力 | 正式位置 | 阶段 |
| --- | --- | --- |
| 后台任务不阻塞 UI | API worker/thread + Qt signals | 5 |
| 会话侧栏和恢复 | desktop session model | 5 |
| 对话、思考折叠区、工具轨迹 | desktop chat widgets | 5 |
| 模型/Ollama 状态 | desktop header/status | 5 |
| 搜索结果表格 | desktop result widget | 5 |
| Excel 文件选择与导出 | desktop action + backend export | 5 |
| 可读的浅/深色样式 | desktop stylesheet | 5 |
| PyCharm 开发热更新 | `scripts/dev/run-desktop-agent.ps1` | 5 |
| Windows exe | PyInstaller spec/build script | 6 |

旧 UI 生成文件不复制到新界面；保留字段显示和导出行为，交互重新设计为类似
Codex 的会话式 Agent 工作台。

## 6. 完成定义

只有同时满足以下条件，实验能力才可标记“已迁移”：

1. 正式模块不导入 `experiments`。
2. 关键业务逻辑有离线单元测试。
3. 真实 Ollama/Chroma 路径有可选 smoke test 或手工验证命令。
4. PyCharm 可以分别运行 backend 和 desktop 入口。
5. README 写明开发、数据构建和 Windows 打包命令。
6. 实验脚本保留为历史材料，或改成调用正式模块的薄演示入口。
