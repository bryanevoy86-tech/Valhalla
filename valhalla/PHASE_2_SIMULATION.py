#!/usr/bin/env python3
"""
PHASE 2 — Revenue Simulation (Read-only)
Purpose: "If this were real, would it make money?"

- NO outbound actions
- NO writes to sandbox DB
- Reads SQLite/CSV artifacts and produces projections
- Conservative/Expected/Aggressive bands (defensible, configurable)

Outputs:
- PHASE_2_report_<timestamp>.txt
- PHASE_2_projection_<timestamp>.csv
"""

from __future__ import annotations

import csv
import glob
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_ASSUMPTIONS = {
    "leads_per_day_fallback": 150,
    "cost_per_lead_usd": 1.50,
    "spread_usd": {"conservative": 6000, "expected": 10000, "aggressive": 14000},
    "score_to_close_prob": [
        {"score_gte": 90, "p_close": 0.20},
        {"score_gte": 80, "p_close": 0.12},
        {"score_gte": 70, "p_close": 0.07},
        {"score_gte": 60, "p_close": 0.04},
        {"score_gte": 50, "p_close": 0.02},
        {"score_gte": 0, "p_close": 0.005},
    ],
    "band_multipliers": {
        "conservative": {"p_mult": 0.75, "spread_mult": 0.90},
        "expected": {"p_mult": 1.00, "spread_mult": 1.00},
        "aggressive": {"p_mult": 1.15, "spread_mult": 1.05},
    },
}


@dataclass
class LeadRow:
    lead_id: str
    score: float
    source: str = ""


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def find_repo_root() -> Path:
    return Path(__file__).resolve().parent


def load_assumptions(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / "ops" / "phase2_assumptions.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] Failed to parse {path}: {e}. Using defaults.")
    return DEFAULT_ASSUMPTIONS


def discover_export_csv(repo_root: Path) -> List[Path]:
    # Prefer our guaranteed exports first
    export_dir = repo_root / "ops" / "exports"
    paths = sorted(export_dir.glob("sandbox_leads_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return paths


def discover_sqlite_files(repo_root: Path) -> List[Path]:
    patterns = ["**/*.db", "**/*.sqlite", "**/*.sqlite3"]
    found: List[Path] = []
    for pat in patterns:
        found.extend([Path(p) for p in glob.glob(str(repo_root / pat), recursive=True)])
    found_sorted = sorted(found, key=lambda p: ("sandbox" not in p.name.lower(), len(str(p))))
    return found_sorted


def discover_csv_files(repo_root: Path) -> List[Path]:
    patterns = ["**/*lead*.csv", "**/*metric*.csv", "**/*pipeline*.csv"]
    found: List[Path] = []
    for pat in patterns:
        found.extend([Path(p) for p in glob.glob(str(repo_root / pat), recursive=True)])

    def rank(p: Path) -> Tuple[int, int]:
        s = str(p).lower()
        return (0 if "ops" in s else 1, len(s))

    return sorted(found, key=rank)


def sqlite_list_tables(db_path: Path) -> List[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def sqlite_try_extract_leads(db_path: Path) -> List[LeadRow]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        tables = sqlite_list_tables(db_path)
        lead_tables = [t for t in tables if "lead" in t.lower()]
        candidate_tables = lead_tables if lead_tables else tables

        for table in candidate_tables:
            try:
                cols = [r["name"] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
                if not cols:
                    continue

                id_col = next((c for c in cols if c.lower() in ("lead_id", "id", "uuid")), cols[0])
                score_col = next(
                    (c for c in cols if c.lower() in ("score", "lead_score", "quality_score", "rank_score", "readiness_score")),
                    None,
                )
                if not score_col:
                    continue

                rows = conn.execute(f"SELECT * FROM '{table}' LIMIT 5000").fetchall()
                leads: List[LeadRow] = []
                for r in rows:
                    raw = dict(r)
                    lead_id = str(raw.get(id_col, "")) or "UNKNOWN"
                    try:
                        score = float(raw.get(score_col, 0.0) or 0.0)
                    except Exception:
                        score = 0.0
                    source = str(raw.get("source", "") or raw.get("lead_source", "") or "")
                    leads.append(LeadRow(lead_id=lead_id, score=score, source=source))
                if leads:
                    return leads
            except Exception:
                continue
        return []
    finally:
        conn.close()


def csv_try_extract_leads(csv_path: Path) -> List[LeadRow]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return []
        fields = [x.lower() for x in reader.fieldnames]

        score_col = None
        for cand in ("score", "lead_score", "quality_score", "rank_score", "readiness_score"):
            if cand in fields:
                score_col = reader.fieldnames[fields.index(cand)]
                break
        if score_col is None:
            return []

        id_col = None
        for cand in ("lead_id", "id", "uuid"):
            if cand in fields:
                id_col = reader.fieldnames[fields.index(cand)]
                break
        if id_col is None:
            id_col = reader.fieldnames[0]

        leads: List[LeadRow] = []
        for row in reader:
            lead_id = str(row.get(id_col, "")) or "UNKNOWN"
            try:
                score = float(row.get(score_col, 0.0) or 0.0)
            except Exception:
                score = 0.0
            source = str(row.get("source", "") or row.get("lead_source", "") or "")
            leads.append(LeadRow(lead_id=lead_id, score=score, source=source))
        return leads


def score_to_prob(score: float, mapping: List[Dict[str, Any]]) -> float:
    # mapping is ordered descending by score_gte (we'll sort defensively)
    mapping_sorted = sorted(mapping, key=lambda x: float(x["score_gte"]), reverse=True)
    for m in mapping_sorted:
        if score >= float(m["score_gte"]):
            return float(m["p_close"])
    return float(mapping_sorted[-1]["p_close"])


def project(leads: List[LeadRow], assumptions: Dict[str, Any]) -> Dict[str, Any]:
    if not leads:
        fallback_n = int(assumptions.get("leads_per_day_fallback", 150))
        avg_score = 60.0
        leads = [LeadRow(lead_id=f"FALLBACK_{i+1}", score=avg_score, source="fallback") for i in range(fallback_n)]

    cost_per_lead = float(assumptions["cost_per_lead_usd"])
    mapping = assumptions["score_to_close_prob"]
    spread = assumptions["spread_usd"]
    mults = assumptions["band_multipliers"]

    total_leads = len(leads)
    avg_score = sum(l.score for l in leads) / max(total_leads, 1)

    bands = ["conservative", "expected", "aggressive"]
    out: Dict[str, Any] = {"bands": {}, "meta": {"total_leads": total_leads, "avg_score": round(avg_score, 2)}}

    for band in bands:
        p_mult = float(mults[band]["p_mult"])
        spread_mult = float(mults[band]["spread_mult"])
        spread_value = float(spread[band]) * spread_mult

        expected_closes = 0.0
        expected_profit = 0.0
        for l in leads:
            p = score_to_prob(l.score, mapping) * p_mult
            p = max(0.0, min(p, 0.95))
            expected_closes += p
            expected_profit += (p * spread_value) - cost_per_lead

        out["bands"][band] = {
            "total_leads_day": total_leads,
            "avg_score": round(avg_score, 2),
            "expected_closes_day": round(expected_closes, 3),
            "spread_used_usd": round(spread_value, 2),
            "cost_per_lead_usd": round(cost_per_lead, 2),
            "expected_profit_day_usd": round(expected_profit, 2),
            "expected_profit_week_usd": round(expected_profit * 7, 2),
            "expected_profit_30d_usd": round(expected_profit * 30, 2),
        }

    return out


def write_outputs(repo_root: Path, stamp: str, results: Dict[str, Any], source_note: str) -> Tuple[Path, Path]:
    report_path = repo_root / f"PHASE_2_report_{stamp}.txt"
    csv_path = repo_root / f"PHASE_2_projection_{stamp}.csv"

    lines: List[str] = []
    lines.append("PHASE 2: REVENUE SIMULATION (READ-ONLY)")
    lines.append("=====================================")
    lines.append(f"UTC Timestamp: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Data Source: {source_note}")
    lines.append("")
    lines.append("Bands (USD):")
    lines.append("------------")

    for band, d in results["bands"].items():
        lines.append(f"[{band.upper()}]")
        lines.append(f"  Leads/day:              {d['total_leads_day']}")
        lines.append(f"  Avg score:              {d['avg_score']}")
        lines.append(f"  Expected closes/day:    {d['expected_closes_day']}")
        lines.append(f"  Spread used (USD):      {d['spread_used_usd']}")
        lines.append(f"  Cost per lead (USD):    {d['cost_per_lead_usd']}")
        lines.append(f"  Profit/day (USD):       {d['expected_profit_day_usd']}")
        lines.append(f"  Profit/week (USD):      {d['expected_profit_week_usd']}")
        lines.append(f"  Profit/30d (USD):       {d['expected_profit_30d_usd']}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "band",
                "leads_day",
                "avg_score",
                "expected_closes_day",
                "spread_used_usd",
                "cost_per_lead_usd",
                "profit_day_usd",
                "profit_week_usd",
                "profit_30d_usd",
            ]
        )
        for band, d in results["bands"].items():
            w.writerow(
                [
                    band,
                    d["total_leads_day"],
                    d["avg_score"],
                    d["expected_closes_day"],
                    d["spread_used_usd"],
                    d["cost_per_lead_usd"],
                    d["expected_profit_day_usd"],
                    d["expected_profit_week_usd"],
                    d["expected_profit_30d_usd"],
                ]
            )

    return report_path, csv_path


def main() -> int:
    repo_root = find_repo_root()
    assumptions = load_assumptions(repo_root)
    stamp = utc_stamp()

    # 1) Prefer our own exports
    exports = discover_export_csv(repo_root)
    if exports:
        leads = csv_try_extract_leads(exports[0])
        source_note = f"csv:{exports[0]}"
        results = project(leads, assumptions)
        report_path, csv_path = write_outputs(repo_root, stamp, results, source_note)
        print("PHASE 2 COMPLETE [OK]")
        print(f"Report: {report_path}")
        print(f"CSV:    {csv_path}")
        print(f"Source: {source_note}")
        return 0

    # 2) Try SQLite
    leads: List[LeadRow] = []
    source_note = "fallback (no artifacts found)"
    for db in discover_sqlite_files(repo_root):
        extracted = sqlite_try_extract_leads(db)
        if extracted:
            leads = extracted
            source_note = f"sqlite:{db}"
            break

    # 3) Try any CSV
    if not leads:
        for c in discover_csv_files(repo_root):
            extracted = csv_try_extract_leads(c)
            if extracted:
                leads = extracted
                source_note = f"csv:{c}"
                break

    results = project(leads, assumptions)
    report_path, csv_path = write_outputs(repo_root, stamp, results, source_note)

    print("PHASE 2 COMPLETE [OK]")
    print(f"Report: {report_path}")
    print(f"CSV:    {csv_path}")
    print(f"Source: {source_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
