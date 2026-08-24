# emc-runtime-local

这是项目当前使用的轻量 Agent Runtime。它只实现现阶段需要的闭环：

```text
用户问题 → Ollama → search_cases → Chroma 案例库 → Ollama 整理方案
```

Runtime 只依赖 `emc-core` 中的端口，不依赖 FastAPI 或 PyQt6。以后接入成熟
harness 时，可以新增另一个 `AgentRuntime` 实现，而不必推翻会话和桌面代码。

## 在 PyCharm 中运行真实链路

新建 Python Run Configuration：

- Script path：`scripts/verify/smoke_agent_runtime.py`
- Working directory：仓库根目录
- Python interpreter：安装了项目依赖的虚拟环境
- Environment variables：把 `packages/emc-core-py/src`、
  `packages/emc-runtime-local-py/src` 和仓库根目录加入 `PYTHONPATH`

也可以在已完成 editable install 的解释器中直接运行：

```powershell
python scripts/verify/smoke_agent_runtime.py
```

脚本会创建 JSONL 会话、调用 Ollama、让模型自主调用 `search_cases`，并把
thinking、工具状态和正式回答流式打印到终端。运行前需启动 Ollama，并确保聊天
模型、`nomic-embed-text` 和案例向量库已经就绪。

## 关键 Python 语法

- `async def` 定义协程；等待 Ollama 和检索 I/O 时不会阻塞整个应用。
- `yield` 把普通函数变成生成器；`async def` 与 `yield` 组合后得到异步生成器。
- `async for` 会逐个消费异步生成器事件，正适合聊天界面的实时更新。
- `isinstance(llm, StreamingLLM)` 依靠 `@runtime_checkable Protocol` 判断 adapter
  是否支持流式能力；旧的 `complete()` 模型替身仍能走兼容路径。

Runtime 每轮只接受一个原生工具调用。这是现阶段有意保留的轻量约束：逻辑容易
观察和测试，也足以完成 EMC 问答；将来确有并行工具需求时再扩展事件协议。
