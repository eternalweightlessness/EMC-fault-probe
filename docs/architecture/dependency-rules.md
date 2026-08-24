# Python 依赖规则

## 1. 允许的依赖方向

```text
apps ──► application services ──► domain / ports
  │                                  ▲
  └──► integrations ─────────────────┘

integrations ──► emc_core ports
emc_runtime_local ──► emc_core
emc_core ──► Python standard library
```

箭头表示“可以导入”。依赖只能向内，领域层不能反向知道 FastAPI、PyQt6、
Ollama 或 ChromaDB。

## 2. 具体规则

1. `emc_core.domain` 不导入应用服务、适配器或应用入口。
2. `emc_core.ports` 只声明 Protocol 和传输模型，不创建具体客户端。
3. `emc_runtime_local` 不读取环境变量，不写死项目路径，不启动 Ollama。
4. `integrations` 不提供 `main()`，也不导入 FastAPI 或 PyQt6。
5. `apps/*/composition.py` 是允许创建具体实现的唯一主要位置。
6. API route 只做请求校验、调用服务和响应转换，不包含业务算法。
7. PyQt6 widget 不访问数据文件、ChromaDB 或 Ollama SDK，只调用 API client。
8. `scripts` 可以调用正式模块，正式模块不得导入 `scripts` 或 `experiments`。
9. `experiments` 可以导入正式模块进行演示；正式代码不得导入实验脚本。

## 3. 为什么使用 Protocol

Python 的 `Protocol` 使用结构化类型：具体类只要提供相同方法，就能满足端口，
不必继承一个框架基类。这样既保留静态检查，也避免把核心代码绑定到某个成熟
harness。

例如，后端构造函数接收 `AgentRuntime`，当前传入 `LocalRuntime`；未来可以传入
`LangGraphRuntime`。这是依赖倒置，而不是在业务代码中编写大量
`if runtime == ...`。

## 4. 自动检查

`scripts/verify/check_architecture.py` 将在实现阶段加入以下检查：

- core 禁止导入 `fastapi`、`PyQt6`、`ollama`、`chromadb`；
- desktop 禁止导入 model/vector-store adapters；
- 正式代码禁止导入 `experiments`；
- integrations 禁止定义应用入口。
