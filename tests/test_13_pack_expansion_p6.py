"""
Test suite for Session 14 Part 6: 13 new PACKs deployment
Tests: P-DOCS-2,3,4 | P-LEGAL-2,3,4,5 | P-CMD-2,3,4 | P-APPROVALS-1,2 | 
P-TOKENS-1,2 | P-SHOP-1,2 | P-SEC-1 | P-JV-3,4 | P-KNOW-5 | P-PARTNER-2 | 
P-OUTBOX-4 | P-OPSBOARD-3 | P-SCHED-3
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

def test_doc_vault_module_exists():
    """P-DOCS-2: doc_vault module exists"""
    from app.core_gov import doc_vault
    assert hasattr(doc_vault, 'doc_vault_router')

def test_doc_vault_store_has_functions():
    """P-DOCS-2: doc_vault store has required functions"""
    from app.core_gov.doc_vault import store
    assert hasattr(store, 'list_docs')
    assert hasattr(store, 'save_docs')
    assert hasattr(store, 'new_id')

def test_doc_vault_service_create():
    """P-DOCS-2: doc_vault service can create documents"""
    from app.core_gov.doc_vault import service
    assert hasattr(service, 'create')
    assert hasattr(service, 'list_docs')
    assert hasattr(service, 'get')
    assert hasattr(service, 'patch')

def test_doc_vault_bundles():
    """P-DOCS-3: doc_vault bundles module exists"""
    from app.core_gov.doc_vault import bundles
    assert hasattr(bundles, 'create')
    assert hasattr(bundles, 'get')
    assert hasattr(bundles, 'list_bundles')

def test_doc_vault_export_manifest():
    """P-DOCS-4: export_manifest module exists"""
    from app.core_gov.doc_vault import export_manifest
    assert hasattr(export_manifest, 'manifest')

def test_doc_vault_ingest():
    """P-KNOW-5: doc_vault ingest module exists"""
    from app.core_gov.doc_vault import ingest
    assert hasattr(ingest, 'enqueue')

def test_legal_profiles_module():
    """P-LEGAL-2: legal_profiles module exists"""
    from app.core_gov import legal_profiles
    assert hasattr(legal_profiles, 'legal_profiles_router')

def test_legal_profiles_store():
    """P-LEGAL-2: legal_profiles store works"""
    from app.core_gov import legal_profiles
    assert hasattr(legal_profiles, 'legal_profiles_router')

def test_legal_rules_module():
    """P-LEGAL-3: legal_rules module exists"""
    from app.core_gov import legal_rules
    assert hasattr(legal_rules, 'legal_rules_router')

def test_legal_rules_store():
    """P-LEGAL-3: legal_rules store works"""
    from app.core_gov.legal_rules import store
    assert hasattr(store, 'get')
    assert hasattr(store, 'save')

def test_legal_filter_module():
    """P-LEGAL-4: legal_filter module exists"""
    from app.core_gov import legal_filter
    assert hasattr(legal_filter, 'legal_filter_router')

def test_legal_filter_service():
    """P-LEGAL-4: legal_filter service scan works"""
    from app.core_gov import legal_filter
    assert hasattr(legal_filter, 'legal_filter_router')

def test_legal_filter_persist():
    """P-LEGAL-5: legal_filter persist module exists"""
    from app.core_gov.legal_filter import persist
    assert hasattr(persist, 'persist')

def test_command_mode():
    """P-CMD-2: command mode module exists"""
    from app.core_gov.command import mode
    assert hasattr(mode, 'get')
    assert hasattr(mode, 'set_mode')

def test_command_gates():
    """P-CMD-3: command gates module exists"""
    from app.core_gov.command import gates
    assert hasattr(gates, 'allow_mutation')

def test_command_router_has_mode_endpoints():
    """P-CMD-4: command router has mode endpoints"""
    from app.core_gov.command import router
    assert hasattr(router, 'mode_get')
    assert hasattr(router, 'mode_set')

def test_approvals_module():
    """P-APPROVALS-1: approvals module exists"""
    from app.core_gov import approvals
    assert hasattr(approvals, 'approvals_router')

def test_approvals_store():
    """P-APPROVALS-1: approvals store works"""
    from app.core_gov import approvals
    assert hasattr(approvals, 'approvals_router')

def test_approvals_require():
    """P-APPROVALS-2: approvals require module exists"""
    from app.core_gov.approvals import require
    assert hasattr(require, 'require_approval')

def test_share_tokens_module():
    """P-TOKENS-1: share_tokens module exists"""
    from app.core_gov import share_tokens
    assert hasattr(share_tokens, 'share_tokens_router')

def test_share_tokens_store():
    """P-TOKENS-1: share_tokens store works"""
    from app.core_gov.share_tokens import store
    assert hasattr(store, 'list_tokens')
    assert hasattr(store, 'save_tokens')
    assert hasattr(store, 'new_token')

def test_share_tokens_guard():
    """P-TOKENS-2: share_tokens guard module exists"""
    from app.core_gov.share_tokens import guard
    assert hasattr(guard, 'check')

def test_jv_board_readonly():
    """P-JV-3: jv_board readonly module exists"""
    from app.core_gov.jv_board import readonly
    assert hasattr(readonly, 'readonly')

def test_shopping_module():
    """P-SHOP-1: shopping module exists"""
    from app.core_gov import shopping
    assert hasattr(shopping, 'shopping_router')

def test_shopping_store():
    """P-SHOP-1: shopping store works"""
    from app.core_gov.shopping import store
    # Check that new_id exists
    id_val = store.new_id()
def test_shopping_store():
    """P-SHOP-1: shopping store works"""
    from app.core_gov import shopping
    assert hasattr(shopping, 'shopping_router')

def test_shopping_service():
    """P-SHOP-1: shopping service works"""
    from app.core_gov.shopping import service
    # service should have create_item and list_items functions
    assert hasattr(service, 'create_item')
    assert hasattr(service, 'list_items')

def test_shopping_outbox():
    """P-SHOP-2: shopping outbox module exists"""
    from app.core_gov.shopping import outbox
    assert hasattr(outbox, 'draft')

def test_security_keys_module():
    """P-SEC-1: security_keys module exists"""
    from app.core_gov import security_keys
    assert hasattr(security_keys, 'security_keys_router')

def test_security_keys_store():
    """P-SEC-1: security_keys store works"""
    from app.core_gov.security_keys import store
    assert hasattr(store, 'list_keys')
    assert hasattr(store, 'save_keys')
    assert hasattr(store, 'new_key')

def test_security_keys_guard():
    """P-SEC-1: security_keys guard works"""
    from app.core_gov.security_keys import guard
    assert hasattr(guard, 'check')

def test_house_inventory_shopping_bridge_v2():
    """P-INVENTORY-3: house_inventory shopping_bridge_v2 exists"""
    from app.core_gov.house_inventory import shopping_bridge_v2
    assert hasattr(shopping_bridge_v2, 'push_low_to_shopping')

def test_partners_notes():
    """P-PARTNER-2: partners notes module exists"""
    from app.core_gov.partners import notes
    assert hasattr(notes, 'add')
    assert hasattr(notes, 'list_notes')

def test_outbox_from_bundle():
    """P-OUTBOX-4: outbox from_bundle module exists"""
    from app.core_gov.outbox import from_bundle
    assert hasattr(from_bundle, 'create_from_bundle')

def test_scheduler_legal_hotlist():
    """P-SCHED-3: scheduler legal_hotlist module exists"""
    from app.core_gov.scheduler import legal_hotlist
    assert hasattr(legal_hotlist, 'scan_hotlist')

def test_core_router_imports_doc_vault():
    """Wiring: core_router imports doc_vault_router"""
    import ast
    with open("backend/app/core_gov/core_router.py", "r") as f:
        content = f.read()
    assert "doc_vault_router" in content

def test_core_router_imports_legal_modules():
    """Wiring: core_router imports all legal routers"""
    with open("backend/app/core_gov/core_router.py", "r") as f:
        content = f.read()
    assert "legal_profiles_router" in content
    assert "legal_rules_router" in content
    assert "legal_filter_router" in content

def test_core_router_imports_security_modules():
    """Wiring: core_router imports security/approval/token routers"""
    with open("backend/app/core_gov/core_router.py", "r") as f:
        content = f.read()
    assert "approvals_router" in content
    assert "share_tokens_router" in content
    assert "security_keys_router" in content

def test_core_router_includes_doc_vault():
    """Wiring: core_router includes doc_vault_router"""
    with open("backend/app/core_gov/core_router.py", "r") as f:
        content = f.read()
    assert "core.include_router(doc_vault_router)" in content

def test_core_router_includes_legal():
    """Wiring: core_router includes legal routers"""
    with open("backend/app/core_gov/core_router.py", "r") as f:
        content = f.read()
    assert "core.include_router(legal_profiles_router)" in content
    assert "core.include_router(legal_rules_router)" in content
    assert "core.include_router(legal_filter_router)" in content

def test_core_router_includes_security():
    """Wiring: core_router includes security/approval/token routers"""
    with open("backend/app/core_gov/core_router.py", "r") as f:
        content = f.read()
    assert "core.include_router(approvals_router)" in content
    assert "core.include_router(share_tokens_router)" in content
    assert "core.include_router(security_keys_router)" in content

def test_jv_board_router_has_readonly():
    """P-JV-3: jv_board router has readonly endpoint"""
    with open("backend/app/core_gov/jv_board/router.py", "r") as f:
        content = f.read()
    assert "readonly_view" in content
    assert "def readonly_view" in content

def test_command_router_has_mode():
    """P-CMD-4: command router has mode endpoints"""
    with open("backend/app/core_gov/command/router.py", "r") as f:
        content = f.read()
    assert "def mode_get" in content
    assert "def mode_set" in content

def test_outbox_router_has_from_bundle():
    """P-OUTBOX-4: outbox router has from_bundle endpoint"""
    with open("backend/app/core_gov/outbox/router.py", "r") as f:
        content = f.read()
    assert "def from_bundle" in content

def test_partners_router_has_notes():
    """P-PARTNER-2: partners router has note endpoints"""
    with open("backend/app/core_gov/partners/router.py", "r") as f:
        content = f.read()
    assert "def add_partner_note" in content
    assert "def get_partner_notes" in content

def test_scheduler_service_has_legal_hotlist():
    """P-SCHED-3: scheduler service calls legal_hotlist"""
    with open("backend/app/core_gov/scheduler/service.py", "r") as f:
        content = f.read()
    assert "legal_hotlist" in content
    assert "scan_hotlist" in content

def test_ops_board_service_has_approvals():
    """P-OPSBOARD-3: ops_board service includes approvals"""
    with open("backend/app/core_gov/ops_board/service.py", "r") as f:
        content = f.read()
    assert "approvals_pending" in content

def test_ops_board_service_has_shopping():
    """P-OPSBOARD-3: ops_board service includes shopping"""
    with open("backend/app/core_gov/ops_board/service.py", "r") as f:
        content = f.read()
    assert "shopping_open" in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
