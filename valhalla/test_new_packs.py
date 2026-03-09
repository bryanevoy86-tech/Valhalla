#!/usr/bin/env python
"""Test that the three new packs (Grants, Loans, Command) compile and wire correctly."""
import sys
sys.path.insert(0, '.')

print("Testing Grants module...")
from app.core_gov.grants.router import router as grants_router
from app.core_gov.grants.store import add_grant, list_grants
from app.core_gov.grants.models import Grant, GrantIn
print("  ✅ Grants imports OK")

print("Testing Loans module...")
from app.core_gov.loans.router import router as loans_router
from app.core_gov.loans.store import add_loan, list_loans
from app.core_gov.loans.models import Loan, LoanIn
from app.core_gov.loans.underwriting import build_underwriting_checklist
from app.core_gov.loans.recommend import recommend_next_step
print("  ✅ Loans imports OK")

print("Testing Command Center module...")
from app.core_gov.command.router import router as command_router
from app.core_gov.command.service import what_now, daily_brief, weekly_review
print("  ✅ Command Center imports OK")

print("Testing core_router wiring...")
from app.core_gov.core_router import core
routes = [r.path for r in core.routes]
has_grants = any("/grants" in r for r in routes)
has_loans = any("/loans" in r for r in routes)
has_command = any("/command" in r for r in routes)

print(f"  ✅ Total routes: {len(routes)}")
print(f"  ✅ /grants endpoint registered: {has_grants}")
print(f"  ✅ /loans endpoint registered: {has_loans}")
print(f"  ✅ /command endpoint registered: {has_command}")

assert has_grants and has_loans and has_command, "Not all new routers registered!"

print("\n✅✅✅ ALL THREE PACKS INSTALLED AND WIRED SUCCESSFULLY ✅✅✅")
