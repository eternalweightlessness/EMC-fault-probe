# EMC Desktop Agent

这是新架构的 PyQt6 对话客户端。它不是旧故障库查询界面的翻版，不包含结果表格
或 Excel 导出；它围绕 Agent 会话、RAG 工具轨迹和流式回答设计。

## PyCharm 运行入口

先安装桌面包：

```powershell
python -m pip install -e apps/desktop-agent
```

然后创建 Python Run Configuration：

- Module name：`emc_desktop_agent.main`
- Working directory：仓库根目录
- Environment：`EMC_BACKEND_URL=http://127.0.0.1:8000/api/v1`

后端未完成装配时，可以独立查看完整 UI 场景：

```powershell
python -m emc_desktop_agent.main --preview
```

## 开发热更新

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/run-desktop-agent.ps1 `
  -Python D:\path\to\python.exe
```

watcher 监视 `apps/desktop-agent/src`。保存 Python、SVG 或 Qt UI 文件后，它只停止
自己启动的桌面子进程并重新打开窗口；后端可以继续使用 Uvicorn 的独立热重载。

## 线程与流式事件

Qt 要求所有 widget 只能在主线程更新。`BackendApiClient` 是同步 HTTP client，
但窗口从不在主线程直接调用它：短请求放进 `RequestWorker(QThread)`，SSE 对话流
由 `StreamWorker(QThread)` 消费，再用 signal 把事件送回主线程。

这里使用 signal/slot 是因为跨线程直接修改 widget 会造成随机崩溃。Python 的
`Protocol` 则让窗口依赖最小 `AgentApi` 接口，测试可注入内存替身，正式运行使用
HTTP client，UI 代码不需要 `if test` 分支。

桌面端识别以下稳定事件：

- `assistant.thinking.delta`：追加到可折叠思考区；
- `tool.requested` / `tool.completed`：创建并更新 RAG 工具卡；
- `assistant.content.delta`：增量渲染 Markdown 回答；
- `assistant.completed`：兼容非流式 adapter 的完整回答；
- `turn.failed`：由后端给出取消或错误状态。

## 视觉回归截图

```powershell
python -m emc_desktop_agent.main --screenshot artifacts/ui/desktop-agent.png
```

该命令使用固定示例会话渲染真实窗口并保存 PNG，适合在修改样式后检查中文字体、
间距、工具卡和不同消息层级。Windows 上若 Conda Qt 未发现系统字体，入口会显式
注册微软雅黑，避免中文显示成方框。
