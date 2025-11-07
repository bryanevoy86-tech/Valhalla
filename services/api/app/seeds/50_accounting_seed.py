"""
Pack 50: Full Accounting Suite - Minimal Chart of Accounts seed
"""
from sqlalchemy.orm import Session
from app.accounting import service as svc


def run(db: Session):
    base = [
        {"code": "1000", "name": "Cash", "type": "asset", "currency": "CAD", "active": True},
        {"code": "1100", "name": "Accounts Receivable", "type": "asset", "currency": "CAD", "active": True},
        {"code": "2000", "name": "Accounts Payable", "type": "liability", "currency": "CAD", "active": True},
        {"code": "3000", "name": "Owner Equity", "type": "equity", "currency": "CAD", "active": True},
        {"code": "4000", "name": "Sales Income", "type": "income", "currency": "CAD", "active": True},
        {"code": "5000", "name": "General Expenses", "type": "expense", "currency": "CAD", "active": True},
        {"code": "5100", "name": "Marketing", "type": "expense", "currency": "CAD", "active": True},
        {"code": "5200", "name": "Contractor Costs", "type": "expense", "currency": "CAD", "active": True},
    ]
    for a in base:
        svc.ensure_account(db, a)
    print("✅ Pack 50: Accounting seed loaded")
