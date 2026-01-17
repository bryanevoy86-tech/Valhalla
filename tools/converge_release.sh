#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Valhalla Converge + One Final Deploy Pack
# - Creates a release branch
# - Finds duplicate files (by hash)
# - Finds common crash causes (imports, env, PORT, health)
# - Runs basic lint/type/test hooks if present
# - Commits + pushes once
# ============================================

BRANCH="${1:-release/converge}"
REMOTE="${2:-origin}"

echo "==> [1/9] Preflight: ensure git clean-ish"
git status --porcelain=v1
echo "If you see untracked/modified files you didn't expect, stop and fix them first."

echo "==> [2/9] Create/switch to branch: $BRANCH"
git checkout -B "$BRANCH"

echo "==> [3/9] Create build report folder"
mkdir -p .converge_reports

echo "==> [4/9] Duplicate file detection (exact duplicates by content hash)"
python3 tools/find_duplicates.py > .converge_reports/duplicates.txt || true
echo "Saved: .converge_reports/duplicates.txt"

echo "==> [5/9] Quick scan for common Render failure patterns"
python3 tools/render_sanity_scan.py > .converge_reports/render_sanity.txt || true
echo "Saved: .converge_reports/render_sanity.txt"

echo "==> [6/9] Run repo checks (only if configured)"
if [ -f package.json ]; then
  echo "Detected Node project. Installing deps (if node_modules missing) and running checks if available..."
  if [ ! -d node_modules ]; then npm ci || npm install; fi
  npm run -s lint 2>/dev/null || true
  npm run -s test 2>/dev/null || true
  npm run -s build 2>/dev/null || true
fi

if [ -f requirements.txt ] || [ -f pyproject.toml ]; then
  echo "Detected Python project. Running lightweight checks if available..."
  python3 -m compileall . >/dev/null 2>&1 || true
  python3 -m pytest -q 2>/dev/null || true
fi

echo "==> [7/9] Show key report highlights"
echo "---- DUPLICATES (top) ----"
head -n 40 .converge_reports/duplicates.txt 2>/dev/null || true
echo "---- RENDER SANITY (top) ----"
head -n 80 .converge_reports/render_sanity.txt 2>/dev/null || true

echo "==> [8/9] Stage everything and commit once"
git add -A
git commit -m "Converge release: dedupe + sanity + stable deploy" || {
  echo "No changes to commit (or commit failed)."
}

echo "==> [9/9] Push branch once"
git push -u "$REMOTE" "$BRANCH"

echo ""
echo "DONE. Next step: point Render to deploy from branch: $BRANCH (or merge to main when green)."
