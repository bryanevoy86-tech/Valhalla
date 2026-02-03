# services/api/tools/public_training/download_sources.py
import os
import sys
import yaml
import pathlib
import requests

def die(msg: str) -> None:
    raise SystemExit(f"[download_sources] {msg}")

def ensure_parent(path: str) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

def download_file(url: str, out_path: str) -> None:
    ensure_parent(out_path)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

def main():
    app_env = os.getenv("APP_ENV", "dev").lower()
    if app_env not in ("sandbox", "dev"):
        die(f"Refusing to download training data in APP_ENV={app_env}. Set APP_ENV=sandbox.")

    cfg_path = os.getenv("PUBLIC_SOURCES_CONFIG", "data/public_sources/sources.yml")
    if not os.path.exists(cfg_path):
        die(f"Missing config: {cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    sources = cfg.get("sources", [])
    if not sources:
        die("No sources found in config.")

    ok = 0
    for s in sources:
        name = s["name"]
        url = s["url"]
        out_path = s["out"]
        kind = s.get("kind", "csv")

        print(f"[download_sources] Fetching {name} ({kind}) -> {out_path}")
        try:
            # StatCan table pages are HTML; we treat that as "manual download fallback"
            # unless the user provides a direct CSV download URL.
            if "statcan" in name and url.endswith("tv.action?pid=1810020501"):
                ensure_parent(out_path)
                print("[download_sources] NOTE: StatCan table is easiest to download manually:")
                print("  - Open the page")
                print("  - Choose 'CSV Download entire table'")
                print(f"  - Save as: {out_path}")
                continue

            download_file(url, out_path)
            ok += 1
        except Exception as e:
            print(f"[download_sources] WARN: Failed {name}: {e}")

    print(f"[download_sources] Done. Successful downloads: {ok}/{len(sources)}")

if __name__ == "__main__":
    main()
