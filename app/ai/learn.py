from __future__ import annotations
import asyncio, os, httpx, pathlib, yaml
from datetime import datetime
from .interlink import Interlink

KNOWLEDGE_DIR = pathlib.Path("app/data/knowledge")
PLANS_DIR = pathlib.Path("app/data/plans")
CONFIG = pathlib.Path("app/config/study_sources.yaml")

async def fetch(url: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.text

async def learn_once() -> dict:
    """Pull study sources → summarize → store notes → propose next tasks."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    inter = Interlink()
    notes = []
    for domain in data.get("domains", []):
        for url in domain.get("sources", []):
            try:
                raw = await fetch(url)
                summary = await inter.summarize(raw[:15000], goal=f"Core insights for {domain['name']}")
                stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                out = KNOWLEDGE_DIR / f"{domain['name'].replace(' ','_')}-{stamp}.md"
                out.write_text(f"# {domain['name']}\nSource: {url}\n\n{summary}\n", encoding="utf-8")
                notes.append((domain["name"], url))
            except Exception as e:
                # keep going on errors and append to errors.log (append mode)
                errfile = KNOWLEDGE_DIR / "errors.log"
                with errfile.open("a", encoding="utf-8") as fh:
                    fh.write(str(e) + "\n")
                continue

    plan_text = await inter.plan("Create next 10 learning tasks to deepen expertise in: " + ", ".join(set(d for d,_ in notes)))
    (PLANS_DIR / "next_tasks.md").write_text(plan_text, encoding="utf-8")
    return {"learned": len(notes), "planned": 10 if notes else 0}
