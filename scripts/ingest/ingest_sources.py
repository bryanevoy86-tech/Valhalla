#!/usr/bin/env python3
import hashlib
import json
import pathlib
import re
import sys
import time
from urllib import robotparser
from urllib.parse import urlparse

import requests
import yaml

ROOT = pathlib.Path(".").resolve()
CATALOG = ROOT / "heimdall/sources/catalog.yaml"
OUTDIR = ROOT / "knowledge"
INDEX = ROOT / "knowledge/index.jsonl"

UA = None
TIMEOUT = 12
DELAY_MS = 600
PER_SOURCE_KEEP = 200


def load_catalog():
    if not CATALOG.exists():
        print(f"Catalog not found: {CATALOG}", file=sys.stderr)
        return {}
    cfg = yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}
    d = cfg.get("defaults", {}) or {}
    global UA, TIMEOUT, DELAY_MS, PER_SOURCE_KEEP
    UA = d.get("user_agent") or "HeimdallBot/1.0"
    TIMEOUT = int(d.get("timeout_seconds", 12))
    DELAY_MS = int(d.get("politeness_delay_ms", 600))
    PER_SOURCE_KEEP = int(d.get("per_source_keep", 200))
    return cfg


def polite_get(url):
    session = requests.Session()
    session.headers["User-Agent"] = UA
    try:
        up = urlparse(url)
        robots_url = f"{up.scheme}://{up.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        if not rp.can_fetch(UA, url):
            return None, f"robots-disallow:{url}"
    except Exception:
        pass
    try:
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code >= 400:
            return None, f"http-{r.status_code}"
        return r, None
    except Exception as e:
        return None, str(e)


def sha(s):
    return hashlib.sha256(s.encode("utf-8", "ignore")).hexdigest()[:16]


def save_doc(category, source_name, title, url, published, content_bytes, ext="txt", meta=None):
    src_slug = re.sub(r"[^a-z0-9\-_.]+", "-", (source_name or "src").lower())
    cdir = OUTDIR / category / src_slug
    cdir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    hid = sha(url or (title or str(ts)))
    fn = f"{ts}_{hid}.{ext}"
    fpath = cdir / fn
    fpath.write_bytes(content_bytes or b"")
    meta = meta or {}
    meta.update(
        {
            "title": title,
            "url": url,
            "published": published,
            "file": str(fpath.relative_to(ROOT)),
            "category": category,
            "source": source_name,
            "ts": ts,
        }
    )
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with INDEX.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(meta) + "\n")
    return fpath


def prune_source(category, source_name):
    src_slug = re.sub(r"[^a-z0-9\-_.]+", "-", (source_name or "src").lower())
    cdir = OUTDIR / category / src_slug
    if not cdir.exists():
        return
    files = sorted(
        [p for p in cdir.glob("*") if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True
    )
    for p in files[PER_SOURCE_KEEP:]:
        try:
            p.unlink()
        except:
            pass


def ingest_rss(cat, src):
    import feedparser

    url = src["url"]
    fp = feedparser.parse(url)
    count = 0
    for e in fp.entries[:50]:
        title = e.get("title") or "(no title)"
        link = e.get("link")
        published = e.get("published") or e.get("updated") or ""
        summary = e.get("summary") or ""
        text = (title + "\n\n" + summary).encode("utf-8", "ignore")
        save_doc(cat, src["name"], title, link, published, text, ext="md", meta={"kind": "rss"})
        count += 1
    prune_source(cat, src["name"])
    return count


def html_to_text(html):
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for bad in soup(["nav", "aside", "script", "style", "footer", "header"]):
            bad.decompose()
        text = soup.get_text("\n", strip=True)
        return text
    except Exception:
        return html


def ingest_web(cat, src):
    r, err = polite_get(src["url"])
    if err or not r:
        return 0
    html = r.text
    title = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    title = title.group(1).strip() if title else src["name"]
    text = html_to_text(html)
    save_doc(
        cat,
        src["name"],
        title,
        src["url"],
        "",
        text.encode("utf-8", "ignore"),
        ext="txt",
        meta={"kind": "web"},
    )
    prune_source(cat, src["name"])
    time.sleep(DELAY_MS / 1000.0)
    return 1


def ingest_github(cat, src):
    repo = src["name"]
    branch = src.get("branch", "main")
    base = f"https://raw.githubusercontent.com/{repo}/{branch}"
    files = ["README.md"]
    cnt = 0
    for path in files:
        url = f"{base}/{path}"
        r, err = polite_get(url)
        if r and r.ok:
            save_doc(
                cat,
                src["name"],
                f"{repo}:{path}",
                url,
                "",
                r.content,
                ext="md",
                meta={"kind": "github"},
            )
            cnt += 1
    prune_source(cat, src["name"])
    time.sleep(DELAY_MS / 1000.0)
    return cnt


def ingest_arxiv(cat, src):
    q = src.get("query", "cat:cs.LG")
    n = int(src.get("max_results", 20))
    url = f"http://export.arxiv.org/api/query?search_query={requests.utils.quote(q)}&start=0&max_results={n}&sortBy=submittedDate&sortOrder=descending"
    r, err = polite_get(url)
    if err or not r:
        return 0
    import feedparser

    fp = feedparser.parse(r.text)
    cnt = 0
    for e in fp.entries:
        title = e.get("title", "arXiv paper")
        link = e.get("link")
        summary = e.get("summary", "")
        published = e.get("published", "")
        text = f"# {title}\n\n{summary}".encode("utf-8", "ignore")
        save_doc(cat, src["name"], title, link, published, text, ext="md", meta={"kind": "arxiv"})
        cnt += 1
    prune_source(cat, src["name"])
    time.sleep(DELAY_MS / 1000.0)
    return cnt


def main():
    cfg = load_catalog()
    cats = cfg.get("categories") or {}
    if not cats:
        print("No categories in catalog.yaml")
        return 0
    total = 0
    for cat, sources in cats.items():
        sources = list(sources or [])[:10]
        for src in sources:
            t = (src.get("type") or "").lower()
            try:
                if t == "rss":
                    total += ingest_rss(cat, src)
                elif t == "web":
                    total += ingest_web(cat, src)
                elif t == "github":
                    total += ingest_github(cat, src)
                elif t == "arxiv":
                    total += ingest_arxiv(cat, src)
                elif t == "youtube":
                    pass
            except Exception as e:
                save_doc(
                    cat,
                    src.get("name", "src"),
                    f"[ingest error] {src.get('name')}",
                    src.get("url", ""),
                    "",
                    str(e).encode("utf-8"),
                    ext="txt",
                    meta={"kind": "error"},
                )
    print(f"Ingest complete. Total docs added: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
