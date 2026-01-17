"""
Pack 50: Full Accounting Suite - Service layer
"""
import os, json, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.accounting.models import (
    Account, Period, JournalEntry, JournalLine, TaxRule, TaxCategory, TaxMapping, ReportRow, CRABotRun
)


def get_account_by_code(db: Session, code: str) -> Account | None:
    return db.query(Account).filter(Account.code==code).first()


def ensure_account(db: Session, acc: dict):
    a = get_account_by_code(db, acc["code"])
    if a:
        return a
    a = Account(**acc)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def post_entry(db: Session, body: dict):
    # Validate lines balance
    total_debit = sum(Decimal(str(l["debit"])) for l in body["lines"])
    total_credit = sum(Decimal(str(l["credit"])) for l in body["lines"])
    balanced = (round(total_debit - total_credit, 2) == 0)
    je = JournalEntry(
        entry_date=datetime.date.fromisoformat(body["entry_date"]),
        memo=body.get("memo"), source=body.get("source"), source_ref=body.get("source_ref")
    )
    db.add(je)
    db.commit()
    db.refresh(je)
    for l in body["lines"]:
        acc = get_account_by_code(db, l["account_code"])
        if not acc:
            raise ValueError(f"Unknown account {l['account_code']}")
        db.add(JournalLine(
            entry_id=je.id, account_id=acc.id,
            debit=Decimal(str(l["debit"])), credit=Decimal(str(l["credit"])),
            tax_code=l.get("tax_code"), tag=l.get("tag")
        ))
    db.commit()
    return je.id, balanced


def _range_from_req(db: Session, req: dict):
    if req.get("period_label"):
        p = db.query(Period).filter(Period.label==req["period_label"]).first()
        if p:
            return p.start_date, p.end_date
    return (
        datetime.date.fromisoformat(req["start_date"]),
        datetime.date.fromisoformat(req["end_date"])
    )


def pnl(db: Session, req: dict):
    start, end = _range_from_req(db, req)
    rows = db.query(JournalLine, Account).join(Account, JournalLine.account_id==Account.id)\
        .join(JournalEntry, JournalLine.entry_id==JournalEntry.id)\
        .filter(JournalEntry.entry_date>=start, JournalEntry.entry_date<=end).all()
    income, expense = {}, {}
    for jl, acc in rows:
        amt = float(jl.credit - jl.debit)
        if acc.type == "income":
            income[acc.name] = income.get(acc.name, 0.0) + amt
        if acc.type == "expense":
            expense[acc.name] = expense.get(acc.name, 0.0) - amt
    income_rows = [{"name": k, "amount": round(v, 2)} for k, v in income.items()]
    expense_rows = [{"name": k, "amount": round(v, 2)} for k, v in expense.items()]
    net = round(sum(income.values()) - sum(expense.values()), 2)
    rep = {
        "currency": os.getenv("ACCOUNTING_BASE_CURRENCY", "CAD"),
        "income": income_rows,
        "expense": expense_rows,
        "net_income": net,
    }
    db.add(ReportRow(kind="pnl", period_label=req.get("period_label") or f"{start}:{end}", payload_json=json.dumps(rep)))
    db.commit()
    return rep


def trial_balance(db: Session, req: dict):
    start, end = _range_from_req(db, req)
    rows = db.query(JournalLine, Account).join(Account, JournalLine.account_id==Account.id)\
        .join(JournalEntry, JournalLine.entry_id==JournalEntry.id)\
        .filter(JournalEntry.entry_date>=start, JournalEntry.entry_date<=end).all()
    agg = {}
    for jl, acc in rows:
        key = f"{acc.code} {acc.name}"
        agg.setdefault(key, {"debit": 0.0, "credit": 0.0})
        agg[key]["debit"] += float(jl.debit)
        agg[key]["credit"] += float(jl.credit)
    rep = {
        "currency": os.getenv("ACCOUNTING_BASE_CURRENCY", "CAD"),
        "rows": [
            {"account": k, "debit": round(v["debit"], 2), "credit": round(v["credit"], 2)}
            for k, v in agg.items()
        ],
    }
    db.add(ReportRow(kind="tb", period_label=req.get("period_label") or f"{start}:{end}", payload_json=json.dumps(rep)))
    db.commit()
    return rep


def tax_report(db: Session, req: dict):
    start, end = _range_from_req(db, req)
    rows = db.query(JournalLine, Account).join(Account, JournalLine.account_id==Account.id)\
        .join(JournalEntry, JournalLine.entry_id==JournalEntry.id)\
        .filter(JournalEntry.entry_date>=start, JournalEntry.entry_date<=end).all()
    totals_by_code, totals_by_category = {}, {}
    cats = {tm.account_id: tm for tm in db.query(TaxMapping).all()}
    cat_names = {c.id: c.name for c in db.query(TaxCategory).all()}
    for jl, acc in rows:
        if jl.tax_code:
            totals_by_code[jl.tax_code] = totals_by_code.get(jl.tax_code, 0.0) + float(jl.debit - jl.credit)
        tm = cats.get(acc.id)
        if tm:
            nm = cat_names.get(tm.tax_category_id, "uncat")
            totals_by_category[nm] = totals_by_category.get(nm, 0.0) + float(jl.debit - jl.credit)
    rep = {
        "totals_by_code": {k: round(v, 2) for k, v in totals_by_code.items()},
        "totals_by_category": {k: round(v, 2) for k, v in totals_by_category.items()},
    }
    db.add(ReportRow(kind="tax", period_label=req.get("period_label") or f"{start}:{end}", payload_json=json.dumps(rep)))
    db.commit()
    return rep


def cra_bot_summary(db: Session, period_label: str, tax_report_payload: dict):
    tol = float(os.getenv("CRA_SAFE_WRITE_OFF_THRESHOLD", "0.7"))
    cat_weights = {c.name: c.risk_weight for c in db.query(TaxCategory).all()}
    score = 0.0
    items = []
    for cat, total in tax_report_payload.get("totals_by_category", {}).items():
        w = cat_weights.get(cat, 0.5)
        # simple presence-based risk
        risk = w
        score += risk
        if w > tol:
            items.append(f"{cat}: high scrutiny (risk={w:.2f}) — keep receipts, mileage, logs.")
    score = round(min(1.0, score / 10.0), 2)
    summary = " | ".join(items) or "All within conservative ranges. Maintain receipts and monthly summaries."
    row = CRABotRun(period_label=period_label, risk_score=score, summary=summary)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"period_label": row.period_label, "risk_score": row.risk_score, "summary": row.summary}
