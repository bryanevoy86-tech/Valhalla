# Valhalla Legacy — Engineering Brief for AI

## What we're building
MVP = Wholesaling + buyer matching + import/export jobs. Non-blocking modules (Shield/FunFund/etc.) are behind feature flags.

## Tech constraints
- Python 3.11+, FastAPI, async endpoints, SQLAlchemy 2.0, Alembic.
- Pydantic v2.
- Worker: async job runner for export_jobs.
- 4-space indent, no tabs.

## Non-negotiables
- Fix runtime errors before refactors.
- Keep public API routes stable unless asked.
- Add/adjust DB migrations with Alembic (no ad-hoc schema drift).

## Common fixes to apply automatically
- Indentation/async misuse in workers.
- Missing imports / dead code.
- Type errors (add typing, prefer `Annotated` for deps).
- Logging instead of bare prints.
- Ensure migrations exist for new/changed columns (e.g., export_jobs.progress/progress_msg/*_at + index).

## Directory expectations
backend/
  app/
    routers/ (FastAPI routes)
    models/  (SQLAlchemy v2)
    schemas/ (Pydantic v2)
    workers/ (export_worker.py)
  alembic/
frontend/ (UI wiring for core flows)

2) Give Copilot Chat the context (one-time “priming”)

Open Copilot Chat and run:

@workspace read ./AI_GUIDE.md
You are a senior engineer on Valhalla Legacy. Follow AI_GUIDE.md strictly. 
Task: scan the repo for issues that violate the guide and propose a staged plan:
1) blocking runtime fixes,
2) migration alignment,
3) lint/format,
4) safe refactors (small PRs).
Output: a checklist with file paths and diffs.

3) Enable auto-fixers so AI + tools clean things up

Add these minimal configs (fast wins):

pyproject.toml

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E","F","I","UP","B"]
fix = true

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
strict = False


.editorconfig

root = true
[*]
indent_style = space
indent_size = 4
end_of_line = lf
insert_final_newline = true


.vscode/settings.json

{
  "python.analysis.typeCheckingMode": "basic",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "ruff.fixOnSave": true
}


pre-commit (optional but great) — .pre-commit-config.yaml

repos:
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks: [{id: black}]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks: [{id: ruff, args: ["--fix"]}]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks: [{id: mypy}]


Then run: pip install pre-commit && pre-commit install

4) Give Copilot precise “sweeps” (copy-paste prompts)

Blocking runtime sweep (workers, imports, crashes)

@workspace
Scan backend/app/workers/export_worker.py and related imports. 
Goal: no crashes. Enforce proper async/await, correct indentation, and exception handling.
If functions are outdented, fix them. Propose a diff only; do not change signatures.
Add logging via structlog or standard logging; remove bare prints.


DB migration alignment

@workspace
Compare models vs DB schema. Ensure export_jobs has:
progress INT NOT NULL DEFAULT 0,
progress_msg TEXT,
started_at TIMESTAMPTZ,
finished_at TIMESTAMPTZ,
and index (status, created_at).
Create/patch an Alembic migration. Output migration file contents and where to place it.


Repo-wide hygiene

@workspace
Run a hygiene pass: remove unused imports, add missing type hints in routers/schemas/models, 
normalize 4-space indent, ensure Pydantic v2 usage, and write small PR-ready diffs grouped by folder.
Respect AI_GUIDE.md. No API breaking changes.


Frontend wiring (MVP)

@workspace
Verify UI supports: auth → dashboard → create lead → create offer → export list/download.
List missing components/pages and the exact API calls each should make.
Propose minimal code snippets to wire them.

5) Lock in “how to change code safely”

Ask Copilot to work in small PRs with titles like:

fix(worker): correct indentation & add error handling

chore(db): alembic migration for export_jobs fields

refactor(api): typing + imports, no API changes

Prompt:

Propose 3 small PRs, each <150 lines, that together remove runtime errors and align schema.
For each PR: show summary, files touched, and full diffs.
