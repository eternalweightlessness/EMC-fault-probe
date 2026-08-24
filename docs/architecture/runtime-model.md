# Agent Runtime 模型

## 1. Runtime 的最小职责

`AgentRuntime` 接收 `AgentState` 并异步产生 `AgentEvent`。它只负责：

- 调用模型；
- 接收模型的工具请求；
- 执行已注册工具；
- 把工具结果回填给模型；
- 在完成、取消、异常或达到步数上限时结束本轮。

配置、会话读写、Ollama 进程管理和 HTTP 响应不属于 runtime。

## 2. 当前实现与未来实现

| 实现 | 状态 | 用途 |
| --- | --- | --- |
| `LocalRuntime` | 当前默认 | 项目自有、易读、支持 Ollama native tool calling |
| Prompt protocol | 兼容迁移 | 只作为不支持 native tools 的模型降级策略 |
| LangGraph/LangChain | 预留 | 复杂图编排出现明确需求后再接入 |
| DeepSeek Harness | 预留 | 需要成熟 coding-agent 能力时再评估 |

## 3. 统一事件

后端、桌面端和未来 harness 必须使用同一事件语义：

| 事件 | 含义 |
| --- | --- |
| `turn.started` | 一轮 Agent 运行开始 |
| `assistant.thinking.delta` | 可选的模型思考增量，只展示和审计 |
| `assistant.content.delta` | 正式回答文本增量 |
| `tool.requested` | 模型请求调用工具 |
| `tool.completed` | 工具成功或失败并返回结果 |
| `assistant.completed` | 正式回答完成 |
| `turn.completed` | 本轮正常结束 |
| `turn.failed` | 取消、异常或步数超限 |

现有 loop 已具备回合和工具事件；流式增量事件在会话/Agent 编排阶段的独立 PR
中补充。`thinking` 可以落盘和显示，但不得回放给模型，避免浪费上下文并影响
后续推理。

## 4. 工具边界

工具分为三层：

1. `ToolSpec`：给模型看的名称、说明和 JSON Schema。
2. handler：实现业务动作的 Python callable。
3. `ToolExecutor`：参数转换、同步/异步兼容和错误归一化。

这种拆分保留实验中装饰器注册表的优点，同时避免让模型直接接触 Python 函数。

## 5. 取消和并发

- 同一会话同一时刻只允许一轮处于运行状态。
- 后端断开 SSE 不应立即删除已持久化的用户消息。
- 用户主动停止时设置取消标志，并产生 `turn.failed(reason=cancelled)`。
- Chroma 同步 I/O 使用工作线程，不能阻塞 asyncio 事件循环。
