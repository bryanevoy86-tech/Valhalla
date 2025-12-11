from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import re
import sys
from typing import Dict, List, Any, Literal, Optional, Tuple, Set

# Folders to search
SEARCH_DIRS = ["app", "backend", "services/api/app"]

# Match lines like:
# PACK CL9 — Decision Outcome Log
# PACK CL10 - Recommendation Feedback & Outcome API
PACK_LINE_RE = re.compile(r"PACK\s+([A-Z0-9]+)\s*[—-]\s*(.+)", re.IGNORECASE)

MANIFEST_PATH = Path("valhalla_manifest.json")

StatusType = Literal["planned", "partial", "complete"]


def load_manifest() -> Dict[str, Any]:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "planned_packs": {},
        "packs": {},
        "generated_at": None,
        "units": {}
    }



def save_manifest(manifest: Dict[str, Any]) -> None:
    manifest["generated_at"] = datetime.utcnow().isoformat() + "Z"
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def classify_component(path: str) -> str:
    """
    Guess what part of the stack this file represents:
    - model / schema / service / router / migration / other
    """
    lower = path.replace("\\", "/").lower()
    if "/models/" in lower:
        return "model"
    if "/schemas/" in lower:
        return "schema"
    if "/services/" in lower and "services/api" not in lower:
        # Only if it's not the api services directory
        return "service"
    if "/services/" in lower and "services/api/app/services/" in lower:
        return "service"
    if "/routers/" in lower:
        return "router"
    if "alembic/versions" in lower:
        return "migration"
    return "other"


def unit_key_for_file(path: str) -> str:
    """
    Create a 'unit key' from a file path.
    Example:
      app/models/deal.py        -> deal
      app/routers/deal.py       -> deal
      app/services/arb_core.py  -> arb_core
    """
    p = Path(path)
    return p.stem  # filename without extension


def scan_files(root: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Scan all .py files in SEARCH_DIRS.

    Returns:
      packs: {
        "CL9": {
          "title": "...",
          "files": [...],
          "components": {...}
        },
        ...
      }

      units: {
        "decision_outcome": {
          "files": [...],
          "components": {...},
          "packs": ["CL9", ...]
        },
        ...
      }
    """
    packs: Dict[str, Dict[str, Any]] = {}
    units: Dict[str, Dict[str, Any]] = {}

    for d in SEARCH_DIRS:
        base = root / d
        if not base.exists():
            continue

        for path in base.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            rel_path = str(path.relative_to(root))
            component = classify_component(rel_path)
            unit_key = unit_key_for_file(rel_path)

            # Ensure unit record exists
            unit = units.setdefault(unit_key, {
                "files": [],
                "components": {
                    "model": False,
                    "schema": False,
                    "service": False,
                    "router": False,
                    "migration": False,
                    "other": False,
                },
                "packs": set(),  # will convert to list before JSON
            })

            unit["files"].append({
                "file": rel_path,
                "component": component,
            })
            if component in unit["components"]:
                unit["components"][component] = True
            else:
                unit["components"]["other"] = True

            # Now scan PACK lines inside this file
            for line_no, line in enumerate(text.splitlines(), start=1):
                m = PACK_LINE_RE.search(line)
                if not m:
                    continue

                pack_id = m.group(1).upper()
                title = m.group(2).strip()

                pack = packs.setdefault(pack_id, {
                    "title": title,
                    "files": [],
                    "components": {
                        "model": False,
                        "schema": False,
                        "service": False,
                        "router": False,
                        "migration": False,
                        "other": False,
                    },
                })

                # keep latest title
                pack["title"] = title

                pack["files"].append({
                    "file": rel_path,
                    "line": line_no,
                    "preview": line.strip(),
                    "component": component,
                })

                if component in pack["components"]:
                    pack["components"][component] = True
                else:
                    pack["components"]["other"] = True

                # link this unit to this pack
                unit["packs"].add(pack_id)

    return packs, units


def auto_status_for_pack(components: Dict[str, bool]) -> StatusType:
    """
    complete if:
      router AND service AND (model OR schema)
    partial if some components exist but not enough for complete
    planned if no components exist
    """
    has_router = components.get("router", False)
    has_service = components.get("service", False)
    has_model = components.get("model", False)
    has_schema = components.get("schema", False)

    if not any(components.values()):
        return "planned"

    if has_router and has_service and (has_model or has_schema):
        return "complete"

    return "partial"


def auto_status_for_unit(components: Dict[str, bool]) -> StatusType:
    """
    Similar heuristic, but for units (even if no PACK header).
    """
    return auto_status_for_pack(components)


def cmd_update(root: Path) -> None:
    """
    Update valhalla_manifest.json with:
      - packs: from PACK headers + components
      - units: every code unit (file stem) + components + linked packs
    """
    manifest = load_manifest()
    planned_packs: Dict[str, Any] = manifest.get("planned_packs", {})
    existing_packs: Dict[str, Any] = manifest.get("packs", {})
    existing_units: Dict[str, Any] = manifest.get("units", {})

    scanned_packs, scanned_units = scan_files(root)

    # --- Update packs ---
    for pack_id, scanned in scanned_packs.items():
        components = scanned["components"]
        title = scanned["title"]

        prev = existing_packs.get(pack_id, {})
        prev_status: Optional[str] = prev.get("status")

        if prev_status in ("planned", "partial", "complete"):
            status: StatusType = prev_status  # type: ignore
        else:
            status = auto_status_for_pack(components)

        existing_packs[pack_id] = {
            "title": title,
            "status": status,
            "components": components,
            "files": scanned["files"],
        }

    # make sure planned packs appear
    for pack_id, info in planned_packs.items():
        pid = pack_id.upper()
        pack_entry = existing_packs.get(pid)
        if not pack_entry:
            existing_packs[pid] = {
                "title": info.get("title", ""),
                "status": info.get("status", "planned"),
                "components": {
                    "model": False,
                    "schema": False,
                    "service": False,
                    "router": False,
                    "migration": False,
                    "other": False,
                },
                "files": [],
            }

    # --- Update units ---
    new_units: Dict[str, Any] = {}
    for unit_id, scanned in scanned_units.items():
        comps = scanned["components"]
        packs_for_unit: Set[str] = scanned.get("packs", set())  # type: ignore

        prev = existing_units.get(unit_id, {})
        prev_status: Optional[str] = prev.get("status")

        if prev_status in ("planned", "partial", "complete"):
            status: StatusType = prev_status  # type: ignore
        else:
            status = auto_status_for_unit(comps)

        new_units[unit_id] = {
            "status": status,
            "components": comps,
            "packs": sorted(list(packs_for_unit)),
            "files": scanned["files"],
        }

    manifest["packs"] = existing_packs
    manifest["planned_packs"] = planned_packs
    manifest["units"] = new_units

    save_manifest(manifest)
    print(f"Updated manifest: {len(scanned_packs)} packs, {len(scanned_units)} units discovered.")


def cmd_summary(root: Path) -> None:
    """
    Print a ChatGPT-ready snapshot:
      - Pack summary (complete/partial/planned)
      - Unit summary (complete/partial/planned)
      - Detailed breakdown of packs and units
    """
    cmd_update(root)
    manifest = load_manifest()

    packs: Dict[str, Any] = manifest.get("packs", {})
    planned_packs: Dict[str, Any] = manifest.get("planned_packs", {})
    units: Dict[str, Any] = manifest.get("units", {})

    # ---- PACK GROUPS ----
    complete_packs, partial_packs, planned_only_packs = [], [], []
    for pid, info in packs.items():
        status = info.get("status", "partial")
        pid_up = pid.upper()
        if status == "complete":
            complete_packs.append(pid_up)
        elif status == "partial":
            partial_packs.append(pid_up)
        else:
            planned_only_packs.append(pid_up)

    complete_packs.sort()
    partial_packs.sort()
    planned_only_packs.sort()

    # Planned but not in code = planned_packs with no components at all
    truly_planned = []
    for pid, info in planned_packs.items():
        pid_up = pid.upper()
        pack_entry = packs.get(pid_up)
        if not pack_entry:
            truly_planned.append(pid_up)
        else:
            comps = pack_entry.get("components", {})
            if not any(comps.values()):
                truly_planned.append(pid_up)
    truly_planned.sort()

    # ---- UNIT GROUPS ----
    complete_units, partial_units, planned_units = [], [], []
    for uid, info in units.items():
        status = info.get("status", "partial")
        if status == "complete":
            complete_units.append(uid)
        elif status == "partial":
            partial_units.append(uid)
        else:
            planned_units.append(uid)

    complete_units.sort()
    partial_units.sort()
    planned_units.sort()

    # ---- OUTPUT ----
    print("\n=== VALHALLA SNAPSHOT (for ChatGPT) ===\n")

    print("PACKS — COMPLETE:")
    print("\n".join(f"  - {p}" for p in complete_packs) or "  (none)")

    print("\nPACKS — PARTIAL:")
    print("\n".join(f"  - {p}" for p in partial_packs) or "  (none)")

    print("\nPACKS — PLANNED ONLY (no code yet or no components):")
    print("\n".join(f"  - {p}" for p in truly_planned) or "  (none)")

    print("\nUNITS (file-based features) — COMPLETE:")
    print("\n".join(f"  - {u}" for u in complete_units) or "  (none)")

    print("\nUNITS — PARTIAL:")
    print("\n".join(f"  - {u}" for u in partial_units) or "  (none)")

    print("\nUNITS — PLANNED (no components):")
    print("\n".join(f"  - {u}" for u in planned_units) or "  (none)")

    print("\n--- PACK DETAILS ---")
    for pid in sorted(packs.keys()):
        info = packs[pid]
        title = info.get("title", "")
        status = info.get("status", "partial")
        comps = info.get("components", {})
        print(f"\n[PACK {pid}] {title}")
        print(f"  status: {status}")
        print("  components:", ", ".join(k for k, v in comps.items() if v) or "(none)")
        for f in info.get("files", []):
            print(
                f"    - {f['file']}:{f['line']} [{f['component']}] :: {f['preview']}"
            )

    print("\n--- UNIT DETAILS ---")
    for uid in sorted(units.keys()):
        info = units[uid]
        status = info.get("status", "partial")
        comps = info.get("components", {})
        packs_for_unit = info.get("packs", [])
        print(f"\n[UNIT {uid}]")
        print(f"  status: {status}")
        print("  packs:", ", ".join(packs_for_unit) or "(none)")
        print("  components:", ", ".join(k for k, v in comps.items() if v) or "(none)")
        for f in info.get("files", []):
            print(f"    - {f['file']} [{f['component']}]")

    print("\n=== END SNAPSHOT ===\n")


def main():
    root = Path(".").resolve()
    if len(sys.argv) < 2:
        print("Usage: python valhalla_pack_tracker.py [update|summary]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "update":
        cmd_update(root)
    elif cmd == "summary":
        cmd_summary(root)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
