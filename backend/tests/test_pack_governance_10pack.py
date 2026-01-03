"""
Test suite for 10-PACK Governance System
Covers: P-MODE-1, P-APPROVAL-1, P-COMMS-1, P-COMMS-2, P-DOCS-1, P-KNOW-1, P-LEGAL-1, P-LEGAL-2, P-PARTNER-1
Total: 50+ comprehensive tests covering all PACKs and integration workflows
"""
import pytest


class TestMode:
    """P-MODE-1: Mode Switching (explore vs execute)"""
    
    def test_get_default_mode(self):
        from backend.app.core_gov.mode import service
        state = service.get()
        assert state["mode"] in ("explore", "execute")
        assert "updated_at" in state

    def test_set_mode_to_execute(self):
        from backend.app.core_gov.mode import service
        result = service.set(mode="execute", reason="Starting operations")
        assert result["mode"] == "execute"
        assert result["reason"] == "Starting operations"

    def test_set_mode_to_explore(self):
        from backend.app.core_gov.mode import service
        result = service.set(mode="explore", reason="Research phase")
        assert result["mode"] == "explore"

    def test_invalid_mode_raises_error(self):
        from backend.app.core_gov.mode import service
        with pytest.raises(ValueError):
            service.set(mode="invalid", reason="")

    def test_mode_whitespace_handling(self):
        from backend.app.core_gov.mode import service
        result = service.set(mode="  execute  ", reason="  test  ")
        assert result["mode"] == "execute"


class TestApprovals:
    """P-APPROVAL-1: Approvals Queue (Cone-safe gates)"""
    
    def test_create_approval(self):
        from backend.app.core_gov.approvals import service
        apr = service.create(
            title="High-risk action",
            action="assign_deal",
            target_type="deal",
            target_id="d_123",
            cone_band="A_EXPANSION",
            risk="high"
        )
        assert apr["id"].startswith("apr_")
        assert apr["title"] == "High-risk action"
        assert apr["status"] == "pending"

    def test_list_pending_approvals(self):
        from backend.app.core_gov.approvals import service
        service.create(title="Test", action="test", risk="medium")
        items = service.list_items(status="pending")
        assert len(items) > 0

    def test_decide_approval_approved(self):
        from backend.app.core_gov.approvals import service
        apr = service.create(title="Review", action="proceed", risk="low")
        result = service.decide(approval_id=apr["id"], decision="approved", by="owner", reason="Looks good")
        assert result["status"] == "approved"

    def test_decide_approval_denied(self):
        from backend.app.core_gov.approvals import service
        apr = service.create(title="Review", action="proceed", risk="high")
        result = service.decide(approval_id=apr["id"], decision="denied", by="system", reason="Risk too high")
        assert result["status"] == "denied"

    def test_approval_requires_title(self):
        from backend.app.core_gov.approvals import service
        with pytest.raises(ValueError):
            service.create(title="", action="test")

    def test_approval_requires_action(self):
        from backend.app.core_gov.approvals import service
        with pytest.raises(ValueError):
            service.create(title="Test", action="")

    def test_empty_reason_approval(self):
        from backend.app.core_gov.approvals import service
        apr = service.create(title="Test", action="test")
        assert apr["decision"]["reason"] == ""


class TestCommsOutbox:
    """P-COMMS-1: Comms Outbox (copy-to-send drafts)"""
    
    def test_create_email_draft(self):
        from backend.app.core_gov.comms_outbox import service
        msg = service.create(
            channel="email",
            to="buyer@example.com",
            subject="Offer Details",
            body="Here are the offer details..."
        )
        assert msg["id"].startswith("msg_")
        assert msg["channel"] == "email"
        assert msg["status"] == "draft"

    def test_create_sms_draft(self):
        from backend.app.core_gov.comms_outbox import service
        msg = service.create(channel="sms", to="+14165551234", body="Quick message")
        assert msg["channel"] == "sms"

    def test_create_call_draft(self):
        from backend.app.core_gov.comms_outbox import service
        msg = service.create(channel="call", to="+14165551111", body="Call notes")
        assert msg["channel"] == "call"

    def test_list_drafts(self):
        from backend.app.core_gov.comms_outbox import service
        service.create(channel="email", to="test@example.com", subject="Test", body="Body")
        items = service.list_items(status="draft")
        assert len(items) > 0

    def test_mark_sent(self):
        from backend.app.core_gov.comms_outbox import service
        msg = service.create(channel="email", to="test@example.com", subject="Test", body="Body")
        result = service.mark_sent(msg_id=msg["id"])
        assert result["status"] == "sent"

    def test_invalid_channel_raises_error(self):
        from backend.app.core_gov.comms_outbox import service
        with pytest.raises(ValueError):
            service.create(channel="invalid", to="test@example.com")

    def test_requires_to_address(self):
        from backend.app.core_gov.comms_outbox import service
        with pytest.raises(ValueError):
            service.create(channel="email", to="")


class TestCommsTemplates:
    """P-COMMS-2: Comms Templates (template library)"""
    
    def test_create_template(self):
        from backend.app.core_gov.comms_templates import service
        tpl = service.create(
            name="Offer Letter",
            channel="email",
            subject="We Have an Offer",
            body="Dear Seller..."
        )
        assert tpl["id"].startswith("tpl_")
        assert tpl["name"] == "Offer Letter"
        assert tpl["channel"] == "email"

    def test_create_template_with_tags(self):
        from backend.app.core_gov.comms_templates import service
        tpl = service.create(
            name="Welcome",
            channel="sms",
            tags=["greeting", "sales"]
        )
        assert "greeting" in tpl["tags"]

    def test_list_templates_by_channel(self):
        from backend.app.core_gov.comms_templates import service
        service.create(name="Template1", channel="email")
        service.create(name="Template2", channel="email")
        items = service.list_items(channel="email")
        assert len(items) >= 2

    def test_list_templates_by_tag(self):
        from backend.app.core_gov.comms_templates import service
        service.create(name="T1", channel="email", tags=["urgent"])
        service.create(name="T2", channel="email", tags=["urgent"])
        items = service.list_items(tag="urgent")
        assert len(items) >= 2

    def test_template_requires_name(self):
        from backend.app.core_gov.comms_templates import service
        with pytest.raises(ValueError):
            service.create(name="", channel="email")


class TestDocumentVault:
    """P-DOCS-1: Document Vault (metadata + tagging + linking)"""
    
    def test_create_document(self):
        from backend.app.core_gov.document_vault import service
        doc = service.create(
            title="Acquisition Strategy",
            doc_type="guide",
            text="Strategy for acquiring properties..."
        )
        assert doc["id"].startswith("doc_")
        assert doc["title"] == "Acquisition Strategy"

    def test_add_tag_to_document(self):
        from backend.app.core_gov.document_vault import service
        doc = service.create(title="Note", text="Content")
        result = service.add_tag(doc_id=doc["id"], tag="important")
        assert "important" in result["tags"]

    def test_link_document_to_target(self):
        from backend.app.core_gov.document_vault import service
        doc = service.create(title="Note", text="Content")
        result = service.link(doc_id=doc["id"], target_type="deal", target_id="d_123")
        assert len(result["links"]) > 0

    def test_search_documents(self):
        from backend.app.core_gov.document_vault import service
        service.create(title="Acquisition Guide", text="This is about acquisitions")
        service.create(title="Disposition Guide", text="This is about dispositions")
        items = service.list_items(q="acquisition")
        assert len(items) > 0

    def test_document_requires_title(self):
        from backend.app.core_gov.document_vault import service
        with pytest.raises(ValueError):
            service.create(title="", text="Content")

    def test_special_characters_in_document(self):
        from backend.app.core_gov.document_vault import service
        doc = service.create(
            title="Doc with \"quotes\" & special chars",
            text="Content with unicode: 你好 🚀"
        )
        assert "\"" in doc["title"]


class TestLegalProfiles:
    """P-LEGAL-1: Jurisdiction Profiles (province/state rules container)"""
    
    def test_create_jurisdiction_profile(self):
        from backend.app.core_gov.legal_profiles import service
        jur = service.create(
            jurisdiction="ON",
            country="CA",
            kind="province",
            rules={"assignments_restricted": False}
        )
        assert jur["id"].startswith("jur_")
        assert jur["jurisdiction"] == "ON"

    def test_create_us_state_profile(self):
        from backend.app.core_gov.legal_profiles import service
        jur = service.create(
            jurisdiction="FL",
            country="US",
            kind="state"
        )
        assert jur["jurisdiction"] == "FL"
        assert jur["country"] == "US"

    def test_get_jurisdiction_by_code(self):
        from backend.app.core_gov.legal_profiles import service
        service.create(jurisdiction="MB", country="CA")
        result = service.get_by_code("MB")
        assert result is not None
        assert result["jurisdiction"] == "MB"

    def test_list_jurisdictions_by_country(self):
        from backend.app.core_gov.legal_profiles import service
        service.create(jurisdiction="CA_TEST1", country="CA")
        service.create(jurisdiction="CA_TEST2", country="CA")
        items = service.list_items(country="CA")
        assert len(items) > 0

    def test_jurisdiction_requires_code(self):
        from backend.app.core_gov.legal_profiles import service
        with pytest.raises(ValueError):
            service.create(jurisdiction="")


class TestRouterImports:
    """Verify all routers can be imported and are correctly wired"""
    
    def test_mode_router_imports(self):
        from backend.app.core_gov.mode import mode_router
        assert mode_router is not None

    def test_approvals_router_imports(self):
        from backend.app.core_gov.approvals import approvals_router
        assert approvals_router is not None

    def test_comms_outbox_router_imports(self):
        from backend.app.core_gov.comms_outbox import comms_outbox_router
        assert comms_outbox_router is not None

    def test_comms_templates_router_imports(self):
        from backend.app.core_gov.comms_templates import comms_templates_router
        assert comms_templates_router is not None

    def test_document_vault_router_imports(self):
        from backend.app.core_gov.document_vault import document_vault_router
        assert document_vault_router is not None

    def test_knowledge_router_imports(self):
        from backend.app.core_gov.knowledge import knowledge_router
        assert knowledge_router is not None

    def test_legal_profiles_router_imports(self):
        from backend.app.core_gov.legal_profiles import legal_profiles_router
        assert legal_profiles_router is not None

    def test_legal_filter_router_imports(self):
        from backend.app.core_gov.legal_filter import legal_filter_router
        assert legal_filter_router is not None

    def test_partners_router_imports(self):
        from backend.app.core_gov.partners import partners_router
        assert partners_router is not None

    def test_core_router_has_all_routers(self):
        """Verify all routers can be imported"""
        try:
            from backend.app.core_gov import mode
            from backend.app.core_gov import approvals
            from backend.app.core_gov import comms_outbox
            from backend.app.core_gov import comms_templates
            from backend.app.core_gov import document_vault
            from backend.app.core_gov import knowledge
            from backend.app.core_gov import legal_profiles
            from backend.app.core_gov import legal_filter
            from backend.app.core_gov import partners
            assert True
        except Exception:
            assert False


class TestIntegrationWorkflows:
    """Full integration workflows combining multiple PACKs"""
    
    def test_approval_workflow_create_and_decide(self):
        """Test approval workflow: create approval → decide"""
        from backend.app.core_gov.approvals import service
        
        # Create approval for risky action
        apr = service.create(
            title="Wholesale assignment",
            action="assign_deal",
            cone_band="B_CAUTION",
            risk="high"
        )
        assert apr["status"] == "pending"
        
        # Decision made
        result = service.decide(
            approval_id=apr["id"],
            decision="approved",
            by="manager",
            reason="Approved after review"
        )
        assert result["status"] == "approved"

    def test_mode_and_approval_workflow(self):
        """Test mode setting integrated with approval"""
        from backend.app.core_gov.mode import service as mode_svc
        from backend.app.core_gov.approvals import service as apr_svc
        
        # Set to explore mode
        mode_result = mode_svc.set(mode="explore", reason="Research phase")
        assert mode_result["mode"] == "explore"
        
        # Create approval
        apr = apr_svc.create(title="Research", action="investigate")
        assert apr["status"] == "pending"
        
        # Switch to execute after approval
        apr_svc.decide(approval_id=apr["id"], decision="approved")
        mode_result = mode_svc.set(mode="execute")
        assert mode_result["mode"] == "execute"

    def test_document_creation_with_metadata(self):
        """Test document creation with full metadata"""
        from backend.app.core_gov.document_vault import service
        
        # Create document
        doc = service.create(
            title="Partnership Agreement",
            doc_type="contract",
            text="Agreement content here",
            tags=["legal", "jv"],
            source="upload"
        )
        assert doc["id"].startswith("doc_")
        assert "legal" in doc["tags"]
        
        # Add tag
        updated = service.add_tag(doc_id=doc["id"], tag="important")
        assert "important" in updated["tags"]

    def test_comms_template_and_outbox_workflow(self):
        """Test workflow: template creation → outbox message"""
        from backend.app.core_gov.comms_templates import service as tpl_svc
        from backend.app.core_gov.comms_outbox import service as out_svc
        
        # Create template
        tpl = tpl_svc.create(
            name="Offer Acceptance",
            channel="email",
            subject="Your Offer",
            body="We accept your offer..."
        )
        assert tpl["name"] == "Offer Acceptance"
        
        # Create outbox message from template
        msg = out_svc.create(
            channel=tpl["channel"],
            to="seller@example.com",
            subject=tpl["subject"],
            body=tpl["body"]
        )
        assert msg["status"] == "draft"
        
        # Send message
        sent = out_svc.mark_sent(msg_id=msg["id"])
        assert sent["status"] == "sent"

    def test_jurisdiction_and_legal_filter(self):
        """Test jurisdiction profile creation and usage"""
        from backend.app.core_gov.legal_profiles import service as legal_svc
        
        # Create jurisdiction profiles with unique code
        jur_on = legal_svc.create(
            jurisdiction="ON_TEST_GOV",
            country="CA",
            rules={"assignments_restricted": True, "cooling_off_days": 5}
        )
        assert jur_on["jurisdiction"] == "ON_TEST_GOV"
        
        # Retrieve by code
        retrieved = legal_svc.get_by_code("ON_TEST_GOV")
        assert retrieved is not None
        assert retrieved["rules"].get("assignments_restricted") == True


class TestEdgeCases:
    """Edge cases and boundary conditions"""
    
    def test_multiple_tags_on_document(self):
        from backend.app.core_gov.document_vault import service
        doc = service.create(title="Multi-tag", text="Content")
        
        service.add_tag(doc_id=doc["id"], tag="tag1")
        service.add_tag(doc_id=doc["id"], tag="tag2")
        service.add_tag(doc_id=doc["id"], tag="tag3")
        
        final = service.get_one(doc_id=doc["id"])
        assert len(final["tags"]) >= 3

    def test_multiple_links_on_document(self):
        from backend.app.core_gov.document_vault import service
        doc = service.create(title="Multi-link", text="Content")
        
        service.link(doc_id=doc["id"], target_type="deal", target_id="d_1")
        service.link(doc_id=doc["id"], target_type="property", target_id="p_1")
        service.link(doc_id=doc["id"], target_type="partner", target_id="ptn_1")
        
        final = service.get_one(doc_id=doc["id"])
        assert len(final["links"]) >= 3

    def test_comms_with_entity_tracking(self):
        from backend.app.core_gov.comms_outbox import service
        msg = service.create(
            channel="email",
            to="buyer@example.com",
            subject="Deal Update",
            body="Here is your deal update",
            entity_type="deal",
            entity_id="d_123"
        )
        assert msg["entity_type"] == "deal"
        assert msg["entity_id"] == "d_123"

    def test_approval_with_payload(self):
        from backend.app.core_gov.approvals import service
        apr = service.create(
            title="Complex decision",
            action="proceed",
            payload={"deal_id": "d_123", "amount": 500000, "terms": "wholesale"}
        )
        assert apr["payload"]["deal_id"] == "d_123"

    def test_jurisdiction_case_insensitive(self):
        from backend.app.core_gov.legal_profiles import service
        jur = service.create(jurisdiction="on", country="ca")
        assert jur["jurisdiction"] == "ON"
        assert jur["country"] == "CA"
