#!/usr/bin/env python3
"""
Valhalla Headless Ops Reporter (single source of truth)
- Pulls /health and /api/governance/runbook/status from your Render API
- Writes ONE output file you can open anytime: ops_status.md (and ops_status.json)
- Also prints a clean "what to do next" section

USAGE:
  1) Save as: ops_report.py
  2) pip install requests
  3) Set env (optional):
       VALHALLA_API_BASE=https://valhalla-api-ha6a.onrender.com
       OPS_OUT_DIR=./ops_out
  4) Run:
       python ops_report.py
  5) Optional: run every 60 seconds:
       python ops_report.py --watch 60
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import requests


@dataclass
class FetchResult:
    ok: bool
    status_code: int
    content_type: str
    json_data: Optional[Dict[str, Any]] = None
    text_snippet: str = ""
    error: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_html_response(content_type: str, text: str) -> bool:
    ct = (content_type or "").lower()
    if "text/html" in ct:
        return True
    # Sometimes proxies mislabel content-type; still detect html by body.
    t = (text or "").lstrip().lower()
    return t.startswith("<!doctype html") or t.startswith("<html")


def safe_snippet(text: str, n: int = 600) -> str:
    if not text:
        return ""
    t = text.replace("\r", "")
    return (t[:n] + ("…" if len(t) > n else "")).strip()


def fetch_json(url: str, timeout: int = 15) -> FetchResult:
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                # Helps avoid some caches returning editor HTML
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        ct = resp.headers.get("content-type", "")
        txt = resp.text or ""

        if is_html_response(ct, txt):
            return FetchResult(
                ok=False,
                status_code=resp.status_code,
                content_type=ct,
                json_data=None,
                text_snippet=safe_snippet(txt),
                error="HTML returned instead of JSON (likely wrong URL, redirect, or proxy page).",
            )

        # Try JSON parsing even if content-type is off.
        try:
            data = resp.json()
            return FetchResult(
                ok=True,
                status_code=resp.status_code,
                content_type=ct,
                json_data=data,
                text_snippet="",
                error="",
            )
        except Exception as e:
            return FetchResult(
                ok=False,
                status_code=resp.status_code,
                content_type=ct,
                json_data=None,
                text_snippet=safe_snippet(txt),
                error=f"Failed to parse JSON: {e}",
            )

    except Exception as e:
        return FetchResult(
            ok=False,
            status_code=0,
            content_type="",
            json_data=None,
            text_snippet="",
            error=str(e),
        )


def normalize_base_url(base: str) -> str:
    base = (base or "").strip()
    if not base:
        return ""
    # Ensure https://
    if base.startswith("http://") or base.startswith("https://"):
        b = base
    else:
        b = "https://" + base
    # Remove trailing slash
    return b.rstrip("/")


def build_urls(base: str) -> Tuple[str, str]:
    health_url = f"{base}/health"
    governance_url = f"{base}/api/governance/runbook/status"
    return health_url, governance_url


def derive_next_actions(health: FetchResult, gov: FetchResult) -> list[str]:
    actions: list[str] = []

    if not health.ok:
        actions.append("Backend health endpoint failing. Check Render logs, env vars, and service status.")
    if not gov.ok:
        actions.append("Governance status failing. Verify endpoint path and that API returns JSON (not HTML).")

    # If governance returns a runbook style object with blockers, surface them.
    if gov.ok and isinstance(gov.json_data, dict):
        data = gov.json_data
        blockers = data.get("blockers") or []
        if blockers:
            # Pull top blocker messages
            top = []
            for b in blockers[:5]:
                msg = b.get("message") or b.get("id") or "blocker"
                detail = b.get("detail")
                if isinstance(detail, dict) and "required" in detail:
                    # Common go-live checklist format
                    req = detail.get("required", {})
                    bc = req.get("backend_complete", {})
                    if isinstance(bc, dict) and bc.get("ok") is False:
                        top.append("Go-live checklist: backend_complete is False → set backend_complete True after final verification.")
                    else:
                        top.append(str(msg))
                else:
                    top.append(str(msg))
            actions.extend([f"Governance blocker: {t}" for t in top])

        ok_to_enable = data.get("ok_to_enable_go_live")
        if ok_to_enable is False:
            actions.append("Do NOT enable go-live yet (ok_to_enable_go_live=false). Clear blockers first.")

    if not actions:
        actions.append("All checks green. Proceed with your next operational step (intake/leads/testing) as planned.")

    return actions


def to_markdown(base: str, health_url: str, gov_url: str, health: FetchResult, gov: FetchResult) -> str:
    def fmt_section(title: str, url: str, res: FetchResult) -> str:
        lines = []
        lines.append(f"## {title}")
        lines.append(f"- URL: `{url}`")
        lines.append(f"- OK: `{res.ok}`")
        lines.append(f"- Status: `{res.status_code}`")
        lines.append(f"- Content-Type: `{res.content_type}`")
        if res.ok and res.json_data is not None:
            pretty = json.dumps(res.json_data, indent=2, ensure_ascii=False)
            lines.append("")
            lines.append("```json")
            lines.append(pretty)
            lines.append("```")
        else:
            if res.error:
                lines.append(f"- Error: `{res.error}`")
            if res.text_snippet:
                lines.append("")
                lines.append("```html")
                lines.append(res.text_snippet)
                lines.append("```")
        lines.append("")
        return "\n".join(lines)

    next_actions = derive_next_actions(health, gov)

    md = []
    md.append(f"# Valhalla Headless Ops Status")
    md.append(f"- Generated (UTC): `{utc_now_iso()}`")
    md.append(f"- API Base: `{base}`")
    md.append("")
    md.append("## What to do next (single source)")
    for a in next_actions:
        md.append(f"- {a}")
    md.append("")
    md.append(fmt_section("Health", health_url, health))
    md.append(fmt_section("Governance / Runbook Status", gov_url, gov))
    return "\n".join(md).strip() + "\n"


def write_outputs(out_dir: str, md_text: str, json_blob: Dict[str, Any]) -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, "ops_status.md")
    js_path = os.path.join(out_dir, "ops_status.json")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    with open(js_path, "w", encoding="utf-8") as f:
        json.dump(json_blob, f, indent=2, ensure_ascii=False)
    return md_path, js_path


def run_once(base: str, out_dir: str) -> int:
    base = normalize_base_url(base)
    if not base:
        print("ERROR: Missing API base. Set VALHALLA_API_BASE or pass --base.")
        return 2

    health_url, gov_url = build_urls(base)

    health = fetch_json(health_url)
    gov = fetch_json(gov_url)

    payload = {
        "generated_at_utc": utc_now_iso(),
        "api_base": base,
        "health": {
            "ok": health.ok,
            "status_code": health.status_code,
            "content_type": health.content_type,
            "json": health.json_data,
            "error": health.error,
            "text_snippet": health.text_snippet,
        },
        "governance": {
            "ok": gov.ok,
            "status_code": gov.status_code,
            "content_type": gov.content_type,
            "json": gov.json_data,
            "error": gov.error,
            "text_snippet": gov.text_snippet,
        },
        "next_actions": derive_next_actions(health, gov),
    }

    md = to_markdown(base, health_url, gov_url, health, gov)
    md_path, js_path = write_outputs(out_dir, md, payload)

    print(f"[OK] Wrote: {md_path}")
    print(f"[OK] Wrote: {js_path}")
    print("")
    print("Next actions:")
    for a in payload["next_actions"]:
        print(f" - {a}")

    # Return non-zero if governance/health failing (useful for scripts)
    if not health.ok or not gov.ok:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.getenv("VALHALLA_API_BASE", "https://valhalla-api-ha6a.onrender.com"))
    parser.add_argument("--out", default=os.getenv("OPS_OUT_DIR", "./ops_out"))
    parser.add_argument("--watch", type=int, default=0, help="Re-run every N seconds (0 = run once).")
    args = parser.parse_args()

    if args.watch and args.watch > 0:
        while True:
            code = run_once(args.base, args.out)
            # keep looping regardless; you want continuous visibility
            time.sleep(args.watch)
    else:
        raise SystemExit(run_once(args.base, args.out))


if __name__ == "__main__":
    main()
