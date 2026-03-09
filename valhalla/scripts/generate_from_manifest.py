#!/usr/bin/env python3
import json
import os
import pathlib
import sys
import time

import yaml

ROOT = pathlib.Path(".").resolve()
MANIFEST = ROOT / "heimdall/roadmap/manifest.json"
QDIR = ROOT / "heimdall/queue"
STATE = ROOT / "heimdall/state/autopilot.json"


def now_ts():
    return int(time.time())


def load_json(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_yaml_atomic(dirpath: pathlib.Path, basename: str, obj: dict) -> str:
    dirpath.mkdir(parents=True, exist_ok=True)
    ts = now_ts()
    tmp = dirpath / f".{basename}_{ts}.tmp"
    final = dirpath / f"{basename}_{ts}.yaml"
    tmp.write_text(yaml.safe_dump(obj, sort_keys=False), encoding="utf-8")
    tmp.replace(final)
    return str(final)


def feature_to_spec(feature: dict, storage_default: str) -> dict:
    name = feature["name"]
    storage = os.getenv("DATABASE_URL") and (feature.get("storage") or storage_default) != "memory"
    storage_kind = "db" if storage else "memory"
    return {
        "type": "spec",
        "name": name,
        "resource": name,
        "storage": storage_kind,
        "fields": feature.get("fields", []),
        "routes": feature.get("routes", []),
    }


def main():
    mf = load_json(MANIFEST, {})
    feats = mf.get("features", [])
    storage_default = (mf.get("defaults", {}) or {}).get("storage", "auto")
    if storage_default not in ("auto", "db", "memory"):
        storage_default = "auto"
    state = load_json(STATE, {"last": {}})
    last = state.get("last", {})
    enqueued = []
    N = int(os.getenv("HEIMDALL_AUTOPILOT_BATCH", "6"))
    count = 0
    for f in feats:
        name = f["name"]
        last_ts = int(last.get(name, 0))
        if time.time() - last_ts < 24 * 3600:
            continue
        spec = feature_to_spec(f, storage_default)
        path = write_yaml_atomic(QDIR, f"spec_{name}", spec)
        enqueued.append(path)
        last[name] = now_ts()
        count += 1
        if count >= N:
            break
    pub = {"type": "publish", "name": "autopilot_bundle", "note": "autopilot periodic"}
    write_yaml_atomic(QDIR, "publish_autopilot", pub)
    state["last"] = last
    save_json(STATE, state)
    out = ROOT / "generated/jobs/generate_from_manifest" / "latest_enqueued.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(enqueued), encoding="utf-8")
    print(f"Enqueued {len(enqueued)} specs; +1 publish")


if __name__ == "__main__":
    sys.exit(main() or 0)
