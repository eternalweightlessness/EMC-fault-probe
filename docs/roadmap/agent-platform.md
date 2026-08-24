# Agent 应用迁移路线图

每个独立板块使用基于 `main` 的分支、独立测试和独立 PR。跨板块的装配工作留在
最后的集成分支，避免未合并分支相互依赖或产生隐式 base。

## 阶段 1：架构和迁移设计

- 分支：`docs/agent-app-architecture`
- 交付：架构总览、依赖规则、runtime 模型、ADR、实验能力迁移表。
- 验收：文档与现有代码一致，每项实验功能有唯一目标位置。

## 阶段 2：后端基础

- 建议分支：`feat/backend-foundation`
- 交付：settings、composition、FastAPI app factory、lifespan、health/models API、
  PyCharm/PowerShell 开发入口。
- 验收：无需 Ollama 即可导入和测试；Ollama 可用时报告真实状态。

## 阶段 3：数据与检索

- 建议分支：`feat/data-search-services`
- 交付：故障案例模型、JSON repository、关键词搜索、向量索引构建和结构化检索
  服务。
- 验收：151 条发布数据可校验、去重和检索；索引构建可重复执行。

## 阶段 4：会话和 Agent 流式服务

- 建议分支：`feat/session-agent-streaming`
- 交付：JSONL session store、Chat Service、流式 runtime 事件、生成取消和 Prompt
  协议降级适配器。
- 验收：能新建/恢复会话并完整跑通 Ollama → tool → Ollama；thinking 不回放。

## 阶段 5：桌面 Agent

- 建议分支：`feat/desktop-agent-ui`
- 交付：Codex 风格会话式 UI、工具轨迹、思考折叠、流式回答、会话历史、运行
  状态和独立热更新启动脚本。
- 验收：PyCharm 可启动；后端重载不关闭 UI；长任务不阻塞 Qt 主线程。

## 阶段 6：Windows 发布和端到端验证

- 建议分支：`build/windows-desktop-release`
- 交付：会话/流式 chat API 的最终装配、PyInstaller spec、资源路径、后端子进程
  管理、构建脚本、README 和 E2E smoke test。
- 验收：干净 Windows 环境可生成并启动 exe；本地 Ollama 不会被应用误杀。

## 后续候选项

- 云端 LLM/Embedding adapters。
- 工作区与受控文件工具。
- 审批、权限和审计日志。
- Web 前端。
- LangGraph、DeepSeek Harness 等成熟 runtime adapters。
