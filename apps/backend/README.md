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

## PowerShell development entry

```powershell
.\scripts\dev\run-backend.ps1
```

The script enables Uvicorn reload mode. Importing `emc_backend.main` does not
start Ollama; set `EMC_AUTO_START_OLLAMA=true` if the backend should own a local
`ollama serve` process.
