# ...existing code...

#!/usr/bin/env python3
import json
import pathlib
import re
from datetime import datetime

ROOT = pathlib.Path(".").resolve()
IDX = ROOT / "knowledge/index.jsonl"
STATE = ROOT / "heimdall/state/knowledge_summaries.json"
OUT = ROOT / "knowledge/summaries"
CATALOG_MD = ROOT / "dist/docs/knowledge_catalog.md"


def sentences(text):
    # light splitter: . ? ! with space or EOL
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    # keep reasonable sentences
    return [s.strip() for s in chunks if 40 <= len(s.strip()) <= 300][:8]


def summarize(text, max_lines=5):
    sents = sentences(text)
    if not sents:
        return text[:600] + ("…" if len(text) > 600 else "")
    # naive “importance” by length & keyword hits
    keywords = set(
        [
            "performance",
            "latency",
            "security",
            "design",
            "pattern",
            "api",
            "database",
            "scale",
            "deploy",
            "test",
            "bug",
            "fix",
            "release",
            "breaking",
        ]
    )
    scored = []
    for s in sents:
        score = min(len(s), 200)
        score += sum(40 for k in keywords if k.lower() in s.lower())
        scored.append((score, s))
    scored.sort(reverse=True)
    pick = [s for _, s in scored[:max_lines]]
    return "• " + "\n• ".join(pick)


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"done": {}}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def build_catalog(rows):
    rows = sorted(rows, key=lambda r: r.get("ts", 0), reverse=True)[:5000]
    lines = [
        "# Knowledge Catalog\n\n_Generated: {}_\n\n".format(
            datetime.now().isoformat(timespec="seconds")
        )
    ]
    cur_cat = None
    for r in rows:
        cat = r.get("category", "uncategorized")
        if cat != cur_cat:
            lines.append(f"\n## {cat}\n")
            cur_cat = cat
        title = r.get("title") or "(untitled)"
        rel = r.get("file") or ""
        url = r.get("url") or ""
        when = r.get("published") or ""
        lines.append(f"- [{title}]({rel})  — {when}  {(' · ' + url) if url else ''}")
    CATALOG_MD.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    st = load_state()
    done = st.get("done", {})
    rows = []
    if not IDX.exists():
        print("no index yet")
        return 0
    with IDX.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    summarized = 0
    for r in rows:
        rel = r.get("file")
        if not rel or rel in done:
            continue
        src = ROOT / rel
        if not src.exists():
            done[rel] = "missing"
            continue
        try:
            raw = src.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            done[rel] = "read_error"
            continue
        summ = summarize(raw)
        out = OUT / r.get("category", "misc") / (r.get("source", "src").lower().replace(" ", "-"))
        out.mkdir(parents=True, exist_ok=True)
        outp = out / (pathlib.Path(rel).name + ".sum.md")
        outp.write_text(f"# {r.get('title') or '(untitled)'}\n\n{summ}\n", encoding="utf-8")
        done[rel] = "ok"
        summarized += 1

    # refresh catalog
    build_catalog(rows)
    st["done"] = done
    save_state(st)
    print(f"summarized={summarized}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
import pathlib

ROOT = pathlib.Path(".").resolve()
IDX = ROOT / "knowledge/index.jsonl"
STATE = ROOT / "heimdall/state/knowledge_summaries.json"
OUT = ROOT / "knowledge/summaries"
CATALOG_MD = ROOT / "dist/docs/knowledge_catalog.md"


def sentences(text):
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in chunks if 40 <= len(s.strip()) <= 300][:8]


def summarize(text, max_lines=5):
    sents = sentences(text)
    if not sents:
        return text[:600] + ("…" if len(text) > 600 else "")
    keywords = set(
        [
            "performance",
            "latency",
            "security",
            "design",
            "pattern",
            "api",
            "database",
            "scale",
            "deploy",
            "test",
            "bug",
            "fix",
            "release",
            "breaking",
        ]
    )
    scored = []
    for s in sents:
        score = min(len(s), 200)
        score += sum(40 for k in keywords if k.lower() in s.lower())
        scored.append((score, s))
    scored.sort(reverse=True)
    pick = [s for _, s in scored[:max_lines]]
    return "• " + "\n• ".join(pick)


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"done": {}}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def build_catalog(rows):
    rows = sorted(rows, key=lambda r: r.get("ts", 0), reverse=True)[:5000]
    lines = [
        "# Knowledge Catalog\n\n_Generated: {}_\n\n".format(
            datetime.now().isoformat(timespec="seconds")
        )
    ]
    cur_cat = None
    for r in rows:
        cat = r.get("category", "uncategorized")
        if cat != cur_cat:
            lines.append(f"\n## {cat}\n")
            cur_cat = cat
        title = r.get("title") or "(untitled)"
        rel = r.get("file") or ""
        url = r.get("url") or ""
        when = r.get("published") or ""
        lines.append(f"- [{title}]({rel})  — {when}  {(' · ' + url) if url else ''}")
    CATALOG_MD.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    st = load_state()
    done = st.get("done", {})
    rows = []
    if not IDX.exists():
        print("no index yet")
        return 0
    with IDX.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    summarized = 0
    for r in rows:
        rel = r.get("file")
        if not rel or rel in done:
            continue
        src = ROOT / rel
        if not src.exists():
            done[rel] = "missing"
            continue
        try:
            raw = src.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            done[rel] = "read_error"
            continue
        summ = summarize(raw)
        out = OUT / r.get("category", "misc") / (r.get("source", "src").lower().replace(" ", "-"))
        out.mkdir(parents=True, exist_ok=True)
        outp = out / (pathlib.Path(rel).name + ".sum.md")
        outp.write_text(f"# {r.get('title') or '(untitled)'}\n\n{summ}\n", encoding="utf-8")
        done[rel] = "ok"
        summarized += 1

    build_catalog(rows)
    st["done"] = done
    save_state(st)
    print(f"summarized={summarized}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
