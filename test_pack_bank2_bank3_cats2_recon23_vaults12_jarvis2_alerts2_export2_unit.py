import pytest
from typing import Dict, Any
import uuid

# ============================================================================
# P-BANK-2: CSV Import Tests
# ============================================================================

def test_csv_parse_basic():
    from backend.app.core_gov.bank import csv_import
    csv_text = "Date,Description,Amount,Account\n2026-01-03,Test,100.00,RBC"
    mapping = {"date": "Date", "description": "Description", "amount": "Amount", "account": "Account"}
    rows = csv_import.parse_csv(csv_text, mapping)
    assert len(rows) == 1
    assert rows[0]["amount"] == 100.0
    assert rows[0]["description"] == "Test"


def test_csv_parse_negative_amount():
    from backend.app.core_gov.bank import csv_import
    csv_text = "Date,Description,Amount\n2026-01-03,Debit,(50.00)"
    mapping = {"date": "Date", "description": "Description", "amount": "Amount"}
    rows = csv_import.parse_csv(csv_text, mapping)
    assert rows[0]["amount"] == -50.0


def test_csv_parse_currency_format():
    from backend.app.core_gov.bank import csv_import
    # Test plain number
    csv_text = "Date,Description,Amount\n2026-01-03,Purchase,1234.56"
    mapping = {"date": "Date", "description": "Description", "amount": "Amount"}
    rows = csv_import.parse_csv(csv_text, mapping)
    assert rows[0]["amount"] == 1234.56
    # Test with dollar sign
    csv_text2 = "Date,Description,Amount\n2026-01-03,Purchase,$1234.56"
    rows2 = csv_import.parse_csv(csv_text2, mapping)
    assert rows2[0]["amount"] == 1234.56


def test_csv_import_endpoint():
    from backend.app.core_gov.bank import service
    csv_text = "Date,Description,Amount\n2026-01-03,CSV Import Test,75.50"
    mapping = {"date": "Date", "description": "Description", "amount": "Amount"}
    from backend.app.core_gov.bank.csv_import import parse_csv
    payloads = parse_csv(csv_text, mapping)
    result = service.bulk_import(payloads)
    assert result["created"] == 1


# ============================================================================
# P-BANK-3: Bank Profiles Tests
# ============================================================================

def test_bank_profiles_create():
    from backend.app.core_gov.bank_profiles import service as psvc
    mapping = {"date": "Date", "description": "Description", "amount": "Amount"}
    rec = psvc.create(name="RBC", mapping=mapping, notes="RBC CSV profile")
    assert rec["id"].startswith("bp_")
    assert rec["name"] == "RBC"


def test_bank_profiles_create_missing_name():
    from backend.app.core_gov.bank_profiles import service as psvc
    with pytest.raises(ValueError, match="name required"):
        psvc.create(name="", mapping={})


def test_bank_profiles_create_invalid_mapping():
    from backend.app.core_gov.bank_profiles import service as psvc
    with pytest.raises(ValueError, match="mapping must be"):
        psvc.create(name="Test", mapping={})


def test_bank_profiles_list():
    from backend.app.core_gov.bank_profiles import service as psvc
    psvc.create(name="Profile1", mapping={"date": "D"})
    items = psvc.list_items()
    assert len(items) > 0


def test_bank_profiles_get_one():
    from backend.app.core_gov.bank_profiles import service as psvc
    rec = psvc.create(name="GetTest", mapping={"test": "field"})
    found = psvc.get_one(rec["id"])
    assert found["name"] == "GetTest"


def test_bank_profiles_get_one_not_found():
    from backend.app.core_gov.bank_profiles import service as psvc
    result = psvc.get_one("bp_nonexistent")
    assert result is None


# ============================================================================
# P-CATS-2: Bank Categorizer Tests
# ============================================================================

def test_bank_categorizer_create_rule():
    from backend.app.core_gov.bank_categorizer import service as bcsvc
    rec = bcsvc.create_rule(name="Superstore", contains="superstore", category="groceries", confidence=0.9)
    assert rec["id"].startswith("bcr_")
    assert rec["category"] == "groceries"


def test_bank_categorizer_list_rules():
    from backend.app.core_gov.bank_categorizer import service as bcsvc
    bcsvc.create_rule(name="Rule1", contains="test1", category="cat1")
    bcsvc.create_rule(name="Rule2", contains="test2", category="cat2", confidence=0.95)
    items = bcsvc.list_rules()
    assert len(items) >= 2


def test_bank_categorizer_categorize_txn_match():
    from backend.app.core_gov.bank_categorizer import service as bcsvc
    bcsvc.create_rule(name="Coffee", contains="coffee", category="dining", confidence=0.85)
    txn = {"description": "Starbucks Coffee Shop", "amount": 5.50}
    res = bcsvc.categorize_txn(txn)
    assert res["category"] == "dining"
    assert res["confidence"] == 0.85


def test_bank_categorizer_categorize_txn_no_match():
    from backend.app.core_gov.bank_categorizer import service as bcsvc
    txn = {"description": "Unknown Transaction", "amount": 100}
    res = bcsvc.categorize_txn(txn)
    assert res["category"] == ""
    assert res["confidence"] == 0.0


# ============================================================================
# P-RECON-2: Auto-Accept Threshold Rules Tests
# ============================================================================

def test_recon_auto_accept_no_suggestions():
    from backend.app.core_gov.reconcile import auto_accept
    result = auto_accept.auto_accept(bank_txn_id="nonexistent", threshold=0.92)
    assert result["accepted"] == False
    assert "no suggestions" in result.get("warnings", [])


def test_recon_auto_accept_below_threshold():
    from backend.app.core_gov.reconcile import auto_accept
    result = auto_accept.auto_accept(bank_txn_id="bt_test", threshold=0.99)
    assert result["accepted"] == False


# ============================================================================
# P-RECON-3: Batch Reconcile Runner Tests
# ============================================================================

def test_recon_batch_no_txns():
    from backend.app.core_gov.reconcile import batch
    result = batch.run_batch(limit=10, threshold=0.92)
    assert "accepted" in result
    assert "attempted" in result
    assert "failures" in result


# ============================================================================
# P-VAULTS-1: Sinking Funds Tests
# ============================================================================

def test_vaults_create():
    from backend.app.core_gov.vaults import service as vsvc
    rec = vsvc.create(name="Rent Buffer", target=1000.0, balance=500.0, category="bills")
    assert rec["id"].startswith("v_")
    assert rec["name"] == "Rent Buffer"
    assert float(rec["target"]) == 1000.0


def test_vaults_create_missing_name():
    from backend.app.core_gov.vaults import service as vsvc
    with pytest.raises(ValueError, match="name required"):
        vsvc.create(name="", target=100)


def test_vaults_list():
    from backend.app.core_gov.vaults import service as vsvc
    vsvc.create(name="Vault1", target=1000)
    items = vsvc.list_items()
    assert len(items) > 0


def test_vaults_deposit():
    from backend.app.core_gov.vaults import service as vsvc
    vault = vsvc.create(name="DepositTest", balance=100)
    updated = vsvc.deposit(vault["id"], amount=50, note="test deposit")
    assert float(updated["balance"]) == 150.0


def test_vaults_withdraw():
    from backend.app.core_gov.vaults import service as vsvc
    vault = vsvc.create(name="WithdrawTest", balance=200)
    updated = vsvc.withdraw(vault["id"], amount=50, note="test withdraw")
    assert float(updated["balance"]) == 150.0


def test_vaults_patch():
    from backend.app.core_gov.vaults import service as vsvc
    vault = vsvc.create(name="PatchTest", target=500)
    patched = vsvc.patch(vault["id"], {"target": 1000, "notes": "Updated target"})
    assert float(patched["target"]) == 1000.0


# ============================================================================
# P-VAULTS-2: Vault Allocator Tests
# ============================================================================

def test_vaults_allocator_suggest_funding():
    from backend.app.core_gov.vaults import allocator
    result = allocator.suggest_funding(days=30)
    assert "plan" in result
    assert "obligations_est" in result
    assert "shopping_est" in result


# ============================================================================
# P-JARVIS-2: Finance Brief Tests
# ============================================================================

def test_finance_brief_structure():
    from backend.app.core_gov.command import finance_brief
    result = finance_brief.finance_brief(month="2026-01")
    assert result["month"] == "2026-01"
    assert "actuals" in result
    assert "bank_unreconciled_count" in result
    assert "upcoming_14_days" in result
    assert "vault_funding_suggestion" in result


def test_finance_brief_defaults_to_today():
    from backend.app.core_gov.command import finance_brief
    result = finance_brief.finance_brief()
    assert result["month"]  # should have a month value


# ============================================================================
# P-ALERTS-2: Finance Alerts Tests
# ============================================================================

def test_finance_alerts_run_checks():
    from backend.app.core_gov.finance_alerts import service as asvc
    result = asvc.run_checks(unreconciled_threshold=500)
    assert "alerts" in result
    assert "warnings" in result
    assert "today" in result


def test_finance_alerts_run_with_threshold():
    from backend.app.core_gov.finance_alerts import service as asvc
    result = asvc.run_checks(unreconciled_threshold=10)
    # Result should have alerts field
    assert isinstance(result["alerts"], list)


# ============================================================================
# P-EXPORT-2: CSV Export Tests
# ============================================================================

def test_export_csv_receipts():
    from backend.app.core_gov.export_csv import service as esvc
    result = esvc.receipts_csv(limit=100)
    assert "csv" in result
    assert "warnings" in result
    assert isinstance(result["csv"], str)


def test_export_csv_bank():
    from backend.app.core_gov.export_csv import service as esvc
    result = esvc.bank_csv(status="new", limit=100)
    assert "csv" in result
    assert "warnings" in result


def test_export_csv_monthly_report():
    from backend.app.core_gov.export_csv import service as esvc
    result = esvc.monthly_report_csv(month="2026-01")
    assert "csv" in result
    assert "warnings" in result


# ============================================================================
# Integration & Workflow Tests
# ============================================================================

def test_csv_import_and_bank_workflow():
    """Test: import CSV → create bank txn → list"""
    from backend.app.core_gov.bank import csv_import, service as bsvc
    
    csv_text = "Date,Description,Amount,Account,ID\n2026-01-03,Integration Test,99.99,RBC,ext123"
    mapping = {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "account": "Account",
        "external_id": "ID"
    }
    payloads = csv_import.parse_csv(csv_text, mapping)
    result = bsvc.bulk_import(payloads, dedupe_external_id=True)
    assert result["created"] >= 0


def test_bank_categorizer_workflow():
    """Test: create rule → categorize txn"""
    from backend.app.core_gov.bank_categorizer import service as bcsvc
    
    bcsvc.create_rule(name="Restaurant", contains="mcdonald", category="dining", confidence=0.9)
    txn = {"description": "McDonald's Fast Food", "amount": 15.00}
    result = bcsvc.categorize_txn(txn)
    assert result["category"] == "dining"


def test_vault_workflow():
    """Test: create vault → deposit → withdraw → list"""
    from backend.app.core_gov.vaults import service as vsvc
    
    vault = vsvc.create(name=f"Workflow_{uuid.uuid4().hex[:8]}", target=1000, balance=500)
    vsvc.deposit(vault["id"], 200)
    vsvc.withdraw(vault["id"], 100)
    items = vsvc.list_items()
    assert len(items) > 0


def test_bank_profile_and_csv_workflow():
    """Test: create profile → import CSV with profile mapping"""
    from backend.app.core_gov.bank_profiles import service as psvc
    from backend.app.core_gov.bank.csv_import import parse_csv
    
    mapping = {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "account": "Account"
    }
    profile = psvc.create(name=f"Workflow_{uuid.uuid4().hex[:8]}", mapping=mapping)
    
    csv_text = "Date,Description,Amount,Account\n2026-01-03,Test,50,Checking"
    rows = parse_csv(csv_text, profile["mapping"])
    assert len(rows) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
