# EMC Backend

FastAPI backend for the local EMC Fault Probe Agent.

## Install for development

From the repository root:

```powershell
python -m pip install -e packages/emc-core-py `
    -e packages/emc-runtime-local-py `
    -e integrations `
    -e "apps/backend[test]"
```

Editable installs keep imports working from any current directory while still
loading the source files you edit in PyCharm.

## PyCharm entry

Create a **Python** run configuration:

- Module name: `emc_backend.main`
- Parameters: `--reload`
- Working directory: repository root
- Environment variable: `EMC_PROJECT_ROOT=<repository root>`
- Add these source roots in the project structure:
  - `apps/backend/src`
  - `packages/emc-core-py/src`
  - `packages/emc-runtime-local-py/src`

Run `emc_backend.main`, then open:

- API docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>
- Models: <http://127.0.0.1:8000/api/v1/models>
- Sessions: <http://127.0.0.1:8000/api/v1/sessions>

The desktop uses the session endpoints to create and restore chats. Posting a
message to `/api/v1/sessions/{session_id}/messages` returns Server-Sent Events
for thinking deltas, RAG tool calls and answer deltas; cancellation is available
at `/api/v1/sessions/{session_id}/cancel`.

## PowerShell development entry

```powershell
.\scripts\dev\run-backend.ps1
```

The script enables Uvicorn reload mode. Importing `emc_backend.main` does not
start Ollama; set `EMC_AUTO_START_OLLAMA=true` if the backend should own a local
`ollama serve` process. Set `EMC_OLLAMA_THINK=false` when a smaller model should
skip visible reasoning and return the final answer faster. All supported values
are listed in the repository `.env.example`.
