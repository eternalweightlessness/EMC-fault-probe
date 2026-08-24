# EMC Fault Probe Agent 架构总览

## 1. 当前阶段的目标

本项目先实现一个可以独立运行、容易理解的本地 Agent 应用，再为成熟
Agent harness 保留适配接口。当前阶段不引入 LangGraph、LangChain 或
DeepSeek Harness；业务代码只依赖项目自己的端口（Protocol），具体运行时由
应用的 `composition.py` 组装。

项目提供两个正式运行入口：

- `apps/backend`：FastAPI 后端，负责会话、Agent 运行、检索和运行状态。
- `apps/desktop-agent`：PyQt6 桌面客户端，开发时连接热重载后端，发布时可用
  PyInstaller 打包为 Windows 应用。

`experiments` 只保留研究过程和回归样例，不再作为正式应用入口。

产品主流程是一个轻量 EMC 专业对话 Agent：用户描述问题，模型按需调用
`search_cases` 检索本地案例知识库，再结合命中资料给出诊断思路和整改方案。
桌面端展示会话、流式回答、思考状态和工具轨迹，而不是复刻旧数据库查询界面。

## 2. 运行结构

```text
PyQt6 Desktop
    │ HTTP + Server-Sent Events
    ▼
FastAPI Backend
    │ application services
    ▼
emc_core ports and domain models
    │
    ├── emc_runtime_local.LocalRuntime
    ├── integrations.models.ollama
    ├── integrations.vector_stores.chroma
    └── JSON / JSONL persistence adapters
```

桌面端不直接导入 Ollama、ChromaDB 或 runtime。这个边界使开发模式与未来的
Windows 打包模式使用同一套 API，也让 Web 客户端可以复用后端。

## 3. 代码区域的职责

| 区域 | 职责 | 不应包含 |
| --- | --- | --- |
| `packages/emc-core-py` | 领域模型、应用服务、端口、工具定义 | FastAPI、PyQt6、Ollama SDK |
| `packages/emc-runtime-local-py` | 项目自有的轻量 Agent loop | 配置读取、数据库路径、UI |
| `integrations` | Ollama、Chroma 和未来 harness 的适配器 | 应用入口、页面状态 |
| `apps/backend` | 配置、依赖组装、HTTP/SSE API | 具体检索算法、UI |
| `apps/desktop-agent` | 桌面交互、API client、视图状态 | 直接调用模型或向量库 |
| `scripts` | 开发、数据构建、验证和打包命令 | 可复用业务逻辑 |
| `experiments` | 可追溯的实验代码 | 生产入口 |

## 4. 请求的主流程

1. 桌面端创建或选择一个会话。
2. 用户消息通过后端 API 写入 JSONL 会话存储。
3. Chat Service 恢复不含 `thinking` 的模型历史，创建 `AgentState`。
4. `AgentRuntime` 产生统一事件；本阶段由 `LocalRuntime` 实现。
5. 模型需要资料时调用 `search_cases`，工具通过 `Retriever` 端口检索。
6. 后端一边持久化事件，一边通过 SSE 推送给桌面端。
7. UI 分开展示回答、思考状态和工具轨迹；模型历史只回放正式回答。

## 5. 为成熟 harness 保留的替换点

后端只持有 `AgentRuntime`，不判断具体 runtime 类型。未来接入成熟框架时新增
`integrations/agent-runtimes/<name>/runtime.py`，实现同一个端口，并在
`composition.py` 根据配置选择即可。领域模型、工具、会话存储和 UI API 不随
harness 更换而改变。

## 6. 暂不实现的范围

- 云端模型 API、账号系统和远程多租户部署。
- 任意命令执行、任意文件写入等高风险通用 Agent 工具。
- LangGraph/LangChain/DeepSeek Harness 的正式接入。
- 自动更新器和 Windows 安装包签名。
- 旧 PyQt6 程序的结果表格、Excel 导出和数据库管理式页面。

这些能力只有在本地 Ollama 主流程稳定后才进入后续 ADR 和独立 PR。
