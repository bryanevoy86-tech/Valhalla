import pytest
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

# Bank module tests
def test_bank_create_txn():
    from backend.app.core_gov.bank import service as bsvc
    payload = {
        "date": "2026-01-03",
        "description": "RBC Bill Payment",
        "amount": 87.22,
        "txn_type": "debit",
        "account": "RBC chequing"
    }
    rec = bsvc.create(payload)
    assert rec["id"].startswith("bt_")
    assert rec["date"] == "2026-01-03"
    assert rec["description"] == "RBC Bill Payment"
    assert float(rec["amount"]) == 87.22
    assert rec["status"] == "new"
    assert rec["created_at"]
    assert rec["updated_at"]


def test_bank_create_missing_date():
    from backend.app.core_gov.bank import service as bsvc
    with pytest.raises(ValueError, match="date is required"):
        bsvc.create({"description": "test", "amount": 100})


def test_bank_create_missing_description():
    from backend.app.core_gov.bank import service as bsvc
    with pytest.raises(ValueError, match="description is required"):
        bsvc.create({"date": "2026-01-03", "amount": 100})


def test_bank_list_txns():
    from backend.app.core_gov.bank import service as bsvc
    # Create a txn
    bsvc.create({"date": "2026-01-03", "description": "Test", "amount": 50.0})
    items = bsvc.list_txns()
    assert len(items) > 0
    assert items[0]["id"].startswith("bt_")


def test_bank_list_txns_by_status():
    from backend.app.core_gov.bank import service as bsvc
    # Create and filter by status
    rec = bsvc.create({"date": "2026-01-03", "description": "Test", "amount": 50.0})
    filtered = bsvc.list_txns(status="new")
    assert any(x["id"] == rec["id"] for x in filtered)


def test_bank_get_one():
    from backend.app.core_gov.bank import service as bsvc
    rec = bsvc.create({"date": "2026-01-03", "description": "GetOneTest", "amount": 75.0})
    found = bsvc.get_one(rec["id"])
    assert found["id"] == rec["id"]
    assert found["description"] == "GetOneTest"


def test_bank_get_one_not_found():
    from backend.app.core_gov.bank import service as bsvc
    result = bsvc.get_one("bt_nonexistent")
    assert result is None


def test_bank_patch_txn():
    from backend.app.core_gov.bank import service as bsvc
    rec = bsvc.create({"date": "2026-01-03", "description": "PatchTest", "amount": 100.0})
    patched = bsvc.patch(rec["id"], {"status": "reconciled", "notes": "Updated"})
    assert patched["status"] == "reconciled"
    assert patched["notes"] == "Updated"
    assert patched["updated_at"] > rec["created_at"]


def test_bank_patch_not_found():
    from backend.app.core_gov.bank import service as bsvc
    with pytest.raises(KeyError):
        bsvc.patch("bt_nonexistent", {"status": "reconciled"})


def test_bank_bulk_import():
    from backend.app.core_gov.bank import service as bsvc
    payloads = [
        {"date": "2026-01-01", "description": "Import1", "amount": 10.0},
        {"date": "2026-01-02", "description": "Import2", "amount": 20.0},
        {"date": "2026-01-03", "description": "Import3", "amount": 30.0},
    ]
    result = bsvc.bulk_import(payloads)
    assert result["created"] == 3
    assert result["skipped"] == 0
    assert len(result["items"]) == 3


def test_bank_bulk_import_dedupe():
    from backend.app.core_gov.bank import service as bsvc
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    payloads = [
        {"date": "2026-01-01", "description": "Dup1", "amount": 10.0, "external_id": f"EXT_{unique_id}_1"},
        {"date": "2026-01-01", "description": "Dup1", "amount": 10.0, "external_id": f"EXT_{unique_id}_1"},
    ]
    result = bsvc.bulk_import(payloads, dedupe_external_id=True)
    assert result["created"] == 1
    assert result["skipped"] == 1


# Reconcile module tests
def test_recon_suggest_no_match():
    from backend.app.core_gov.reconcile import service as rsvc
    result = rsvc.suggest(bank_txn_id="nonexistent_txn", max_suggestions=10)
    assert result["bank_txn_id"] == "nonexistent_txn"
    assert result["suggestions"] == []
    assert "bank txn not found" in result["warnings"]


def test_recon_link_validation():
    from backend.app.core_gov.reconcile import service as rsvc
    # Test invalid target_type
    with pytest.raises(ValueError, match="target_type must be"):
        rsvc.link("bt_123", "invalid_type", "rc_123")


def test_recon_link_missing_txn_id():
    from backend.app.core_gov.reconcile import service as rsvc
    with pytest.raises(ValueError, match="bank_txn_id required"):
        rsvc.link("", "receipt", "rc_123")


def test_recon_link_missing_target_id():
    from backend.app.core_gov.reconcile import service as rsvc
    with pytest.raises(ValueError, match="target_id required"):
        rsvc.link("bt_123", "receipt", "")


def test_recon_link_create():
    from backend.app.core_gov.reconcile import service as rsvc
    rec = rsvc.link("bt_123", "receipt", "rc_456", note="manual match")
    assert rec["id"].startswith("rl_")
    assert rec["bank_txn_id"] == "bt_123"
    assert rec["target_type"] == "receipt"
    assert rec["target_id"] == "rc_456"
    assert rec["note"] == "manual match"
    assert rec["created_at"]


def test_recon_list_links():
    from backend.app.core_gov.reconcile import service as rsvc
    # Create two links
    rsvc.link("bt_101", "receipt", "rc_201", note="link1")
    rsvc.link("bt_102", "payment", "p_301", note="link2")
    # List all
    all_links = rsvc.list_links()
    assert len(all_links) >= 2
    # List by bank_txn_id
    filtered = rsvc.list_links(bank_txn_id="bt_101")
    assert all(x["bank_txn_id"] == "bt_101" for x in filtered)


# Proofpacks module tests
def test_proofpacks_create_missing_obligation():
    from backend.app.core_gov.proofpacks import service as psvc
    with pytest.raises(KeyError, match="obligation not found"):
        psvc.create_autopay_proof_pack("nonexistent_obligation", bank="RBC")


def test_proofpacks_list_items():
    from backend.app.core_gov.proofpacks import service as psvc
    items = psvc.list_items()
    assert isinstance(items, list)


def test_proofpacks_list_items_by_obligation():
    from backend.app.core_gov.proofpacks import service as psvc
    items = psvc.list_items(obligation_id="ob_123")
    # Should return list, even if empty
    assert isinstance(items, list)


def test_proofpacks_patch_attachments_not_found():
    from backend.app.core_gov.proofpacks import service as psvc
    with pytest.raises(KeyError, match="proof pack not found"):
        psvc.patch_attachments("pp_nonexistent", [{"doc_id": "d1"}])


# Networth module tests
def test_networth_create_asset():
    from backend.app.core_gov.networth import service as nsvc
    payload = {
        "name": "Savings Account",
        "kind": "asset",
        "value": 5000.0,
        "category": "cash"
    }
    rec = nsvc.create_item(payload)
    assert rec["id"].startswith("nw_")
    assert rec["name"] == "Savings Account"
    assert rec["kind"] == "asset"
    assert float(rec["value"]) == 5000.0
    assert rec["status"] == "active"


def test_networth_create_liability():
    from backend.app.core_gov.networth import service as nsvc
    payload = {
        "name": "Car Loan",
        "kind": "liability",
        "value": 15000.0,
        "category": "debt"
    }
    rec = nsvc.create_item(payload)
    assert rec["kind"] == "liability"
    assert float(rec["value"]) == 15000.0


def test_networth_create_missing_name():
    from backend.app.core_gov.networth import service as nsvc
    with pytest.raises(ValueError, match="name is required"):
        nsvc.create_item({"kind": "asset", "value": 100})


def test_networth_create_invalid_kind():
    from backend.app.core_gov.networth import service as nsvc
    with pytest.raises(ValueError, match="kind must be"):
        nsvc.create_item({"name": "Test", "kind": "invalid"})


def test_networth_list_items():
    from backend.app.core_gov.networth import service as nsvc
    nsvc.create_item({"name": "Item1", "kind": "asset", "value": 100})
    nsvc.create_item({"name": "Item2", "kind": "liability", "value": 50})
    items = nsvc.list_items()
    assert len(items) >= 2


def test_networth_list_items_by_status():
    from backend.app.core_gov.networth import service as nsvc
    nsvc.create_item({"name": "Active", "kind": "asset", "value": 100, "status": "active"})
    active = nsvc.list_items(status="active")
    assert any(x["name"] == "Active" for x in active)


def test_networth_patch_item():
    from backend.app.core_gov.networth import service as nsvc
    rec = nsvc.create_item({"name": "PatchTest", "kind": "asset", "value": 1000})
    patched = nsvc.patch(rec["id"], {"value": 2000.0, "notes": "Updated value"})
    assert float(patched["value"]) == 2000.0
    assert patched["notes"] == "Updated value"


def test_networth_patch_not_found():
    from backend.app.core_gov.networth import service as nsvc
    with pytest.raises(KeyError, match="item not found"):
        nsvc.patch("nw_nonexistent", {"value": 100})


def test_networth_snapshot():
    from backend.app.core_gov.networth import service as nsvc
    # Create fresh assets and liabilities
    nsvc.create_item({"name": "TestAsset_Snap", "kind": "asset", "value": 10000, "status": "active"})
    nsvc.create_item({"name": "TestLiability_Snap", "kind": "liability", "value": 3000, "status": "active"})
    snap = nsvc.snapshot(note="test snapshot")
    assert snap["id"].startswith("ns_")
    # Just verify structure - actual totals depend on pre-existing data
    assert snap["asset_total"] >= 0
    assert snap["liability_total"] >= 0
    assert isinstance(snap["net_worth"], float)
    assert snap["note"] == "test snapshot"
    assert "breakdown" in snap
    assert "assets" in snap["breakdown"]
    assert "liabilities" in snap["breakdown"]


def test_networth_list_snapshots():
    from backend.app.core_gov.networth import service as nsvc
    nsvc.snapshot(note="snap1")
    nsvc.snapshot(note="snap2")
    snaps = nsvc.list_snapshots(limit=10)
    assert len(snaps) >= 2


# Exports year-end module tests
def test_yearend_build_invalid_year():
    from backend.app.core_gov.exports_year_end import service as esvc
    with pytest.raises(ValueError, match="year must be"):
        esvc.build(1900)


def test_yearend_build_future_year_out_of_range():
    from backend.app.core_gov.exports_year_end import service as esvc
    with pytest.raises(ValueError, match="year must be"):
        esvc.build(2200)


def test_yearend_build_valid():
    from backend.app.core_gov.exports_year_end import service as esvc
    result = esvc.build(2026, currency="CAD")
    assert result["id"].startswith("ye_")
    assert "export" in result
    export = result["export"]
    assert export["year"] == 2026
    assert export["currency"] == "CAD"
    assert "totals" in export
    assert "by_month" in export
    assert "receipt_by_category" in export
    assert "receipt_by_risk" in export
    assert "counts" in export
    assert isinstance(export["warnings"], list)


def test_yearend_list_items():
    from backend.app.core_gov.exports_year_end import service as esvc
    esvc.build(2026)
    items = esvc.list_items(limit=10)
    assert isinstance(items, list)


# Integration-like tests
def test_bank_txn_workflow():
    """Test basic bank transaction workflow: create -> list -> get -> patch"""
    from backend.app.core_gov.bank import service as bsvc
    
    # Create
    payload = {"date": "2026-01-05", "description": "Workflow Test", "amount": 123.45}
    rec = bsvc.create(payload)
    txn_id = rec["id"]
    
    # List
    items = bsvc.list_txns()
    assert any(x["id"] == txn_id for x in items)
    
    # Get
    found = bsvc.get_one(txn_id)
    assert found["amount"] == 123.45
    
    # Patch
    patched = bsvc.patch(txn_id, {"status": "reconciled"})
    assert patched["status"] == "reconciled"
    
    # Verify
    refetched = bsvc.get_one(txn_id)
    assert refetched["status"] == "reconciled"


def test_networth_workflow():
    """Test networth workflow: create items -> snapshot -> list snapshots"""
    from backend.app.core_gov.networth import service as nsvc
    
    # Create multiple items with unique names to avoid conflicts
    import uuid
    suffix = uuid.uuid4().hex[:8]
    asset_rec = nsvc.create_item({"name": f"House_{suffix}", "kind": "asset", "value": 500000})
    liab_rec = nsvc.create_item({"name": f"Mortgage_{suffix}", "kind": "liability", "value": 400000})
    
    # Take snapshot
    snap = nsvc.snapshot(note="Workflow snapshot")
    
    # Verify snapshot structure (don't assert exact values since other items may exist)
    assert snap["id"].startswith("ns_")
    assert isinstance(snap["net_worth"], float)
    assert snap["asset_total"] >= 500000
    assert snap["liability_total"] >= 400000
    
    # List snapshots
    snaps = nsvc.list_snapshots(limit=5)
    assert any(x["id"] == snap["id"] for x in snaps)


def test_reconcile_link_workflow():
    """Test reconciliation link creation and retrieval"""
    from backend.app.core_gov.reconcile import service as rsvc
    
    # Create link
    rec = rsvc.link("bt_test123", "receipt", "rc_test456", note="test link")
    link_id = rec["id"]
    
    # List by bank txn
    links = rsvc.list_links(bank_txn_id="bt_test123")
    assert any(x["id"] == link_id for x in links)
    
    # Verify properties
    found = [x for x in links if x["id"] == link_id][0]
    assert found["target_type"] == "receipt"
    assert found["target_id"] == "rc_test456"


def test_yearend_export_structure():
    """Verify year-end export has correct structure"""
    from backend.app.core_gov.exports_year_end import service as esvc
    
    result = esvc.build(2026)
    export = result["export"]
    
    # Check all required fields
    assert isinstance(export["totals"]["receipts_total"], float)
    assert isinstance(export["totals"]["payments_total"], float)
    assert isinstance(export["totals"]["grand_total"], float)
    assert isinstance(export["by_month"], dict)
    assert isinstance(export["receipt_by_category"], dict)
    assert isinstance(export["receipt_by_risk"], dict)
    
    # Risk bands should all be present
    for band in ["safe", "medium", "aggressive", "unknown"]:
        assert band in export["receipt_by_risk"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
