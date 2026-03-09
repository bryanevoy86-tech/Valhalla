from __future__ import annotations
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="data/exports", help="Exports directory to prune")
    ap.add_argument("--days", type=int, default=14, help="Delete files older than N days")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    ap.add_argument("--apply", action="store_true", help="Actually delete")
    return ap.parse_args()

def main():
    args = parse_args()
    root = Path(args.path)
    if not root.exists():
        print(f"[INFO] Path not found: {root}")
        return

    if args.apply and args.dry_run:
        raise SystemExit("Choose either --dry-run or --apply, not both.")

    cutoff = datetime.utcnow() - timedelta(days=args.days)
    deleted = 0
    considered = 0

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        considered += 1
        mtime = datetime.utcfromtimestamp(p.stat().st_mtime)
        if mtime < cutoff:
            if args.dry_run:
                print("[DRY] delete:", p)
            elif args.apply:
                try:
                    p.unlink()
                    deleted += 1
                except Exception as e:
                    print("[WARN] failed delete:", p, e)

    mode = "DRY-RUN" if args.dry_run else ("APPLY" if args.apply else "NOOP")
    print(f"\n[{mode}] considered={considered} deleted={deleted} cutoff_days={args.days}")

if __name__ == "__main__":
    main()
