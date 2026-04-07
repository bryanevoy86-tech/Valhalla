Daily developer workflow — Valhalla

Quickstart (Windows PowerShell)

1) Create venv & install

```powershell
cd "C:\Users\Lanna\OneDrive\Documents\4. Important docs\valhalla"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r services\api\requirements.txt
```

2) Run dev server (use this when developing locally)

```powershell
# foreground (logs visible)
.\.venv\Scripts\python.exe -m uvicorn valhalla.services.api.main:app --reload --port 4000

# detached (from another terminal)
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","valhalla.services.api.main:app","--reload","--port","4000"
```

3) Test endpoints

```powershell
# PowerShell
Invoke-RestMethod http://127.0.0.1:4000/api/health | ConvertTo-Json -Depth 5

# curl + jq (if you have them)
curl -s http://127.0.0.1:4000/api/health | jq
```

VS Code workflow

- Open the repo in VS Code.
- Press Ctrl/Cmd+Shift+B to see tasks: Install deps, Run, Format, Lint, Type, Test.
- Use the Run panel -> "FastAPI: Debug" to start the app with breakpoints and hot reload.
- Use the snippets: `fget`, `fpost`, `fbg` to scaffold endpoints quickly.
- Use `api.http` (REST Client) or the built-in HTTP client extensions to hit endpoints without leaving VS Code.

Pre-commit/checklist

- Run `make all` (or the tasks) before committing to run format, lint, type-check, and tests.

Ngrok (when Render is down or for external testing)

```powershell
# expose local port 4000 to the internet
ngrok http 4000

# query the local ngrok API to get the public URL
Invoke-RestMethod http://127.0.0.1:4040/api/tunnels | ConvertTo-Json -Depth 5
```

CI

- A GitHub Actions workflow is included at `.github/workflows/ci.yml`. It runs tests on pushes/PRs against `main`.

That's it — follow this checklist each day and you'll have a fast, reproducible dev loop.