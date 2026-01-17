from __future__ import annotations
import sys
import argparse
import json
from pathlib import Path

# Add valhalla root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ops.capabilities.suggest import suggest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("context", help="Natural language context for Heimdall suggestions")
    ap.add_argument("--max", type=int, default=3)
    args = ap.parse_args()

    results = suggest(args.context, max_suggestions=args.max)
    print(json.dumps({"suggestions": results}, indent=2))


if __name__ == "__main__":
    main()
