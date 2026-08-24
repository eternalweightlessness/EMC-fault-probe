# emc-core

`emc-core` 保存与界面、HTTP 框架和具体模型无关的 Agent 核心代码。桌面端、
后端 API 和测试脚本都应调用这里的应用服务，而不是直接依赖 Ollama 或 Chroma。

## 当前职责

- `domain/`：会话、消息和统一 Agent 事件等纯数据对象。
- `ports/`：`AgentRuntime`、`SessionStore` 等可替换接口。
- `application/`：会话管理和一轮对话的应用编排。
- `persistence/`：当前轻量 JSONL 会话存储。
- `tools/`：工具定义、注册表和 `search_cases` 工具。

`ChatService.send_message()` 返回 `AsyncIterator[AgentEvent]`。调用方可以使用
`async for` 边接收边渲染 thinking、工具调用和回答，不必等模型生成完整文本。

```python
async for event in chat_service.send_message(
    session_id=session_id,
    content="辐射发射超标怎么整改？",
):
    render(event)
```

这里采用 `Protocol` 描述端口，而不要求实现类继承某个基类。Python 会按对象
是否提供兼容方法来判断其能否使用，这种“结构化类型”让本地 Runtime、未来
harness adapter 和测试替身都能替换，而核心层不需要了解具体实现。

会话暂时采用 JSONL：一行一个 JSON 记录，追加写入、容易检查，进程异常时通常
只影响最后一行。项目规模扩大后可新增数据库版 `SessionStore`，上层服务无需改写。
