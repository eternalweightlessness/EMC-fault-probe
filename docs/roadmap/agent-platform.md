# Agent 应用迁移路线图

每个阶段独立分支、独立测试、独立 PR。后一个阶段只从已经合并的前置阶段创建，
避免长期堆叠造成 base 漂移。

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
- 交付：故障案例模型、JSON repository、关键词搜索、向量索引构建、结构化搜索
  API、Excel 导出。
- 验收：151 条发布数据可校验、去重、检索和导出；索引构建可重复执行。

## 阶段 4：会话和 Agent API

- 建议分支：`feat/session-agent-streaming`
- 交付：JSONL session store、Chat Service、流式 runtime 事件、SSE chat API、取消、
  Prompt 协议降级适配器。
- 验收：能新建/恢复会话并完整跑通 Ollama → tool → Ollama；thinking 不回放。

## 阶段 5：桌面 Agent

- 建议分支：`feat/desktop-agent-ui`
- 交付：Codex 风格会话式 UI、工具轨迹、思考折叠、搜索结果、状态和导出、独立
  热更新启动脚本。
- 验收：PyCharm 可启动；后端重载不关闭 UI；长任务不阻塞 Qt 主线程。

## 阶段 6：Windows 发布和端到端验证

- 建议分支：`build/windows-desktop-release`
- 交付：PyInstaller spec、资源路径、后端子进程管理、构建脚本、README 和 E2E
  smoke test。
- 验收：干净 Windows 环境可生成并启动 exe；本地 Ollama 不会被应用误杀。

## 后续候选项

- 云端 LLM/Embedding adapters。
- 工作区与受控文件工具。
- 审批、权限和审计日志。
- Web 前端。
- LangGraph、DeepSeek Harness 等成熟 runtime adapters。
