"""
Test suite for 10-PACK Operational Workflow System:
P-ENTITY-1 (Entity + Trust Status Tracker), P-ENTITY-2 (Checklist Templates),
P-COMMS-1 (Comms Outbox), P-COMMS-2 (Template Library + Render),
P-JV-1 (JV Deal Links), P-JV-2 (JV Dashboard),
P-LEGAL-3 (Require Docs Enforcement), P-PROP-3 (Repair Worksheet),
P-PROP-4 (Rent Worksheet + DSCR), P-PLAYBOOK-1 (Playbooks + Templates)
"""

import pytest
import uuid

# ============================================================================
# P-ENTITY-1 (Entity + Trust Status Tracker) Tests
# ============================================================================

def test_entity1_create_entity():
    """Test creating an entity."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    
    result = ent_svc.create_entity(
        entity_type="corp",
        name="Test Corp Ltd",
        country="CA",
        region_code="MB",
        status="active"
    )
    
    assert "id" in result
    assert result["entity_type"] == "corp"
    assert result["name"] == "Test Corp Ltd"

def test_entity1_list_entities():
    """Test listing entities with filters."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    
    ent_svc.create_entity(entity_type="corp", name="Corp A")
    ent_svc.create_entity(entity_type="trust", name="Trust A")
    
    corps = ent_svc.list_entities(entity_type="corp")
    assert all(e["entity_type"] == "corp" for e in corps)

def test_entity1_add_task():
    """Test adding a task to an entity."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    
    entity = ent_svc.create_entity(entity_type="corp", name="Corp B")
    entity_id = entity["id"]
    
    task = ent_svc.add_task(
        entity_id=entity_id,
        title="Register incorporation",
        status="open",
        priority="high"
    )
    
    assert "id" in task
    assert task["title"] == "Register incorporation"
    assert task["entity_id"] == entity_id

def test_entity1_set_task_status():
    """Test updating task status."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    
    entity = ent_svc.create_entity(entity_type="corp", name="Corp C")
    task = ent_svc.add_task(entity_id=entity["id"], title="Test Task")
    task_id = task["id"]
    
    updated = ent_svc.set_task_status(task_id=task_id, status="done")
    assert updated["status"] == "done"

# ============================================================================
# P-ENTITY-2 (Checklist Templates + Auto-Followups) Tests
# ============================================================================

def test_entity2_apply_corp_template():
    """Test applying corp checklist template."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    from backend.app.core_gov.entity_checklists import service as checklist_svc
    
    entity = ent_svc.create_entity(entity_type="corp", name="Corp D")
    result = checklist_svc.apply_template(
        entity_id=entity["id"],
        template="corp",
        due_days=21,
        create_followups=False
    )
    
    assert result["tasks_created"] == 5
    assert result["template"] == "corp"

def test_entity2_apply_trust_template():
    """Test applying trust checklist template."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    from backend.app.core_gov.entity_checklists import service as checklist_svc
    
    entity = ent_svc.create_entity(entity_type="trust", name="Trust B")
    result = checklist_svc.apply_template(
        entity_id=entity["id"],
        template="trust",
        create_followups=False
    )
    
    assert result["tasks_created"] == 5
    assert result["template"] == "trust"

def test_entity2_apply_bank_template():
    """Test applying bank KYC checklist template."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    from backend.app.core_gov.entity_checklists import service as checklist_svc
    
    entity = ent_svc.create_entity(entity_type="corp", name="Corp E")
    result = checklist_svc.apply_template(
        entity_id=entity["id"],
        template="bank",
        create_followups=False
    )
    
    assert result["tasks_created"] == 4

# ============================================================================
# P-COMMS-1 (Comms Hub Outbox) Tests
# ============================================================================

def test_comms1_create_message():
    """Test creating a message in outbox."""
    from backend.app.core_gov.comms_outbox import service as comms_svc
    
    result = comms_svc.create(
        channel="email",
        to="test@example.com",
        subject="Test Subject",
        body="Test body content"
    )
    
    assert "id" in result
    assert result["channel"] == "email"
    assert result["status"] == "draft"

def test_comms1_list_messages():
    """Test listing messages with filters."""
    from backend.app.core_gov.comms_outbox import service as comms_svc
    
    comms_svc.create(channel="email", to="a@test.com", subject="Email 1")
    comms_svc.create(channel="sms", to="555-1234", subject="SMS 1")
    
    emails = comms_svc.list_items(channel="email")
    assert all(m["channel"] == "email" for m in emails)

def test_comms1_mark_sent():
    """Test marking message as sent."""
    from backend.app.core_gov.comms_outbox import service as comms_svc
    
    msg = comms_svc.create(channel="email", to="test@test.com")
    msg_id = msg["id"]
    
    updated = comms_svc.mark_sent(msg_id)
    assert updated["status"] == "sent"
    assert updated["sent_at"] != ""

# ============================================================================
# P-COMMS-2 (Template Library + Variable Render) Tests
# ============================================================================

def test_comms2_create_template():
    """Test creating a message template."""
    from backend.app.core_gov.comms_templates import service as tpl_svc
    
    result = tpl_svc.create(
        name="Welcome Email",
        channel="email",
        subject="Welcome {{name}}",
        body="Hi {{name}}, welcome to {{org}}"
    )
    
    assert "id" in result
    assert result["name"] == "Welcome Email"

def test_comms2_render_template():
    """Test rendering a template with variables."""
    from backend.app.core_gov.comms_templates import service as tpl_svc
    
    tpl = tpl_svc.create(
        name="Offer Email",
        channel="email",
        subject="Offer for {{property}}",
        body="We have an offer of ${{price}} for {{property}}"
    )
    
    rendered = tpl_svc.render(tpl, {"property": "123 Main St", "price": "250000"})
    
    assert "123 Main St" in rendered["subject"]
    assert "250000" in rendered["body"]

def test_comms2_list_templates():
    """Test listing templates with filters."""
    from backend.app.core_gov.comms_templates import service as tpl_svc
    
    tpl_svc.create(name="Email Tpl 1", channel="email")
    tpl_svc.create(name="SMS Tpl 1", channel="sms")
    
    emails = tpl_svc.list_items(channel="email")
    assert all(t["channel"] == "email" for t in emails)

# ============================================================================
# P-JV-1 (JV Deal Links + Splits) Tests
# ============================================================================

def test_jv1_link_deal_partner():
    """Test linking a deal to a partner."""
    from backend.app.core_gov.jv_links import service as jv_svc
    
    result = jv_svc.link(
        deal_id=f"deal_{uuid.uuid4().hex[:8]}",
        partner_id=f"pt_{uuid.uuid4().hex[:8]}",
        role="jv",
        split_pct=50
    )
    
    assert "id" in result
    assert result["split_pct"] == 50

def test_jv1_list_links():
    """Test listing JV links."""
    from backend.app.core_gov.jv_links import service as jv_svc
    
    deal_id = f"deal_{uuid.uuid4().hex[:8]}"
    partner_id = f"pt_{uuid.uuid4().hex[:8]}"
    
    jv_svc.link(deal_id=deal_id, partner_id=partner_id, split_pct=50)
    
    links = jv_svc.list_links(deal_id=deal_id)
    assert len(links) > 0

def test_jv1_split_check():
    """Test split percentage check."""
    from backend.app.core_gov.jv_links import service as jv_svc
    
    deal_id = f"deal_{uuid.uuid4().hex[:8]}"
    jv_svc.link(deal_id=deal_id, partner_id=f"pt_{uuid.uuid4().hex[:8]}", split_pct=50)
    jv_svc.link(deal_id=deal_id, partner_id=f"pt_{uuid.uuid4().hex[:8]}", split_pct=50)
    
    check = jv_svc.split_check(deal_id)
    assert check["status"] == "ok"
    assert check["total_split_pct"] == 100.0

def test_jv1_split_over():
    """Test split over 100%."""
    from backend.app.core_gov.jv_links import service as jv_svc
    
    deal_id = f"deal_{uuid.uuid4().hex[:8]}"
    jv_svc.link(deal_id=deal_id, partner_id=f"pt_{uuid.uuid4().hex[:8]}", split_pct=60)
    jv_svc.link(deal_id=deal_id, partner_id=f"pt_{uuid.uuid4().hex[:8]}", split_pct=50)
    
    check = jv_svc.split_check(deal_id)
    assert check["status"] == "over"

# ============================================================================
# P-JV-2 (JV Dashboard) Tests
# ============================================================================

def test_jv2_dashboard():
    """Test JV dashboard aggregation."""
    from backend.app.core_gov.jv_dashboard import service as dashboard_svc
    
    result = dashboard_svc.dashboard()
    
    assert "by_partner" in result
    assert "by_deal" in result
    assert isinstance(result["by_partner"], list)

# ============================================================================
# P-LEGAL-3 (Require Docs Enforcement) Tests
# ============================================================================

def test_legal3_require_docs():
    """Test require_docs enforcement."""
    try:
        from backend.app.core_gov.legal import require_docs
        
        result = require_docs.enforce_require_doc(
            jur_code="MB",
            context={"entity_type": "deals", "entity_id": "deal_123"}
        )
        
        # Verify result structure (may contain warnings if rules unavailable)
        assert "jur_code" in result
        assert "requirements" in result
    except (ImportError, AttributeError):
        pytest.skip("legal require_docs not yet available")

# ============================================================================
# P-PROP-3 (Repair Worksheet) Tests
# ============================================================================

def test_prop3_create_repair_sheet():
    """Test creating a repair worksheet."""
    from backend.app.core_gov.repairs import service as repair_svc
    
    result = repair_svc.create(
        property_id=f"prop_{uuid.uuid4().hex[:8]}",
        title="Roof Repairs",
        line_items=[
            {"category": "roof", "item": "Shingles", "qty": 100, "unit_cost": 5, "labor_cost": 500}
        ]
    )
    
    assert "id" in result
    assert result["title"] == "Roof Repairs"

def test_prop3_total_cost():
    """Test calculating repair total cost."""
    from backend.app.core_gov.repairs import service as repair_svc
    
    sheet = repair_svc.create(
        property_id=f"prop_{uuid.uuid4().hex[:8]}",
        line_items=[
            {"qty": 2, "unit_cost": 100, "labor_cost": 50},
            {"qty": 1, "unit_cost": 200, "labor_cost": 100}
        ]
    )
    
    total = repair_svc.total_cost(sheet)
    assert total == (2*100 + 50) + (1*200 + 100)

def test_prop3_summarize():
    """Test repair worksheet summary."""
    from backend.app.core_gov.repairs import service as repair_svc
    
    prop_id = f"prop_{uuid.uuid4().hex[:8]}"
    repair_svc.create(property_id=prop_id, line_items=[{"qty": 1, "unit_cost": 1000, "labor_cost": 500}])
    
    summary = repair_svc.summarize(prop_id)
    assert summary["grand_total"] == 1500.0

# ============================================================================
# P-PROP-4 (Rent Worksheet + DSCR) Tests
# ============================================================================

def test_prop4_create_rent_sheet():
    """Test creating a rent worksheet."""
    from backend.app.core_gov.rents import service as rent_svc
    
    result = rent_svc.create(
        property_id=f"prop_{uuid.uuid4().hex[:8]}",
        gross_rent=2000,
        other_income=200,
        expenses_monthly={"tax": 300, "insurance": 150},
        loan_pmt_monthly=1000
    )
    
    assert "id" in result
    assert result["gross_rent"] == 2000.0

def test_prop4_noi_calculation():
    """Test NOI calculation."""
    from backend.app.core_gov.rents import service as rent_svc
    
    sheet = rent_svc.create(
        property_id=f"prop_{uuid.uuid4().hex[:8]}",
        gross_rent=2000,
        other_income=200,
        expenses_monthly={"tax": 300, "insurance": 150}
    )
    
    # NOI = (2000 + 200) - (300 + 150) = 1750
    noi = rent_svc._noi(sheet)
    assert noi == 1750.0

def test_prop4_dscr():
    """Test DSCR calculation."""
    from backend.app.core_gov.rents import service as rent_svc
    
    sheet = rent_svc.create(
        property_id=f"prop_{uuid.uuid4().hex[:8]}",
        gross_rent=3000,
        expenses_monthly={"tax": 300},
        loan_pmt_monthly=1000
    )
    
    # NOI = 3000 - 300 = 2700, DSCR = 2700 / 1000 = 2.7
    dscr = rent_svc.dscr(sheet)
    assert abs(dscr - 2.7) < 0.01

def test_prop4_summarize():
    """Test rent summary."""
    from backend.app.core_gov.rents import service as rent_svc
    
    prop_id = f"prop_{uuid.uuid4().hex[:8]}"
    rent_svc.create(property_id=prop_id, gross_rent=2500, loan_pmt_monthly=1000)
    
    summary = rent_svc.summarize(prop_id)
    assert len(summary["items"]) > 0
    assert "dscr" in summary["items"][0]

# ============================================================================
# P-PLAYBOOK-1 (Playbooks + Templates) Tests
# ============================================================================

def test_playbook1_create_playbook():
    """Test creating a playbook."""
    from backend.app.core_gov.playbooks import service as pb_svc
    
    result = pb_svc.create(
        name="Assignment Deal Process",
        category="deals",
        region="US",
        steps=["Step 1", "Step 2"],
        checklist=["Item 1", "Item 2"]
    )
    
    assert "id" in result
    assert result["category"] == "deals"

def test_playbook1_seed_defaults():
    """Test seeding default playbooks."""
    from backend.app.core_gov.playbooks import service as pb_svc
    
    result = pb_svc.seed_defaults()
    assert result["seeded"] == 2

def test_playbook1_list_playbooks():
    """Test listing playbooks with filters."""
    from backend.app.core_gov.playbooks import service as pb_svc
    
    pb_svc.create(name="PB 1", category="deals", region="US")
    pb_svc.create(name="PB 2", category="banking", region="CA")
    
    deals = pb_svc.list_items(category="deals")
    assert all(p["category"] == "deals" for p in deals)

# ============================================================================
# Router Tests (Module Importability)
# ============================================================================

def test_router_entity_tracker():
    """Verify entity_tracker router is importable."""
    from backend.app.core_gov.entity_tracker import router
    assert router is not None

def test_router_entity_checklists():
    """Verify entity_checklists router is importable."""
    from backend.app.core_gov.entity_checklists import router
    assert router is not None

def test_router_comms_outbox():
    """Verify comms_outbox router is importable."""
    from backend.app.core_gov.comms_outbox import router
    assert router is not None

def test_router_comms_templates():
    """Verify comms_templates router is importable."""
    from backend.app.core_gov.comms_templates import router
    assert router is not None

def test_router_jv_links():
    """Verify jv_links router is importable."""
    from backend.app.core_gov.jv_links import router
    assert router is not None

def test_router_jv_dashboard():
    """Verify jv_dashboard router is importable."""
    from backend.app.core_gov.jv_dashboard import router
    assert router is not None

def test_router_repairs():
    """Verify repairs router is importable."""
    from backend.app.core_gov.repairs import router
    assert router is not None

def test_router_rents():
    """Verify rents router is importable."""
    from backend.app.core_gov.rents import router
    assert router is not None

def test_router_playbooks():
    """Verify playbooks router is importable."""
    from backend.app.core_gov.playbooks import router
    assert router is not None

# ============================================================================
# Integration Tests
# ============================================================================

def test_entity_to_checklist_flow():
    """Test full entity creation → checklist application flow."""
    from backend.app.core_gov.entity_tracker import service as ent_svc
    from backend.app.core_gov.entity_checklists import service as checklist_svc
    
    # Create entity
    entity = ent_svc.create_entity(entity_type="corp", name="Workflow Test Corp")
    
    # Apply checklist
    result = checklist_svc.apply_template(
        entity_id=entity["id"],
        template="corp",
        due_days=30,
        create_followups=False
    )
    
    # Verify tasks were created
    tasks = ent_svc.list_tasks(entity_id=entity["id"])
    assert len(tasks) == 5

def test_jv_link_to_dashboard_flow():
    """Test JV link creation → dashboard aggregation."""
    from backend.app.core_gov.jv_links import service as jv_svc
    from backend.app.core_gov.jv_dashboard import service as dashboard_svc
    
    deal_id = f"deal_{uuid.uuid4().hex[:8]}"
    partner_id = f"pt_{uuid.uuid4().hex[:8]}"
    
    # Create JV link
    jv_svc.link(deal_id=deal_id, partner_id=partner_id, role="jv", split_pct=50)
    
    # Get dashboard
    dashboard = dashboard_svc.dashboard()
    
    assert "by_deal" in dashboard
    assert "by_partner" in dashboard

def test_comms_template_to_outbox_flow():
    """Test template rendering → outbox message creation."""
    from backend.app.core_gov.comms_templates import service as tpl_svc
    from backend.app.core_gov.comms_outbox import service as outbox_svc
    
    # Create template
    tpl = tpl_svc.create(
        name="Property Inquiry",
        channel="email",
        subject="Interest in {{property}}",
        body="Hello, interested in {{property}} at {{price}}"
    )
    
    # Render
    rendered = tpl_svc.render(tpl, {"property": "456 Oak Ave", "price": "$300k"})
    
    # Create outbox message from rendered content
    msg = outbox_svc.create(
        channel=rendered["channel"],
        to="buyer@example.com",
        subject=rendered["subject"],
        body=rendered["body"]
    )
    
    assert "456 Oak Ave" in msg["subject"]
    assert "buyer@example.com" == msg["to"]

def test_repairs_and_rents_on_property():
    """Test property with both repair sheet and rent worksheet."""
    from backend.app.core_gov.repairs import service as repair_svc
    from backend.app.core_gov.rents import service as rent_svc
    
    prop_id = f"prop_{uuid.uuid4().hex[:8]}"
    
    # Create repair sheet
    repair_svc.create(
        property_id=prop_id,
        line_items=[{"qty": 1, "unit_cost": 5000, "labor_cost": 1000}]
    )
    
    # Create rent sheet
    rent_svc.create(
        property_id=prop_id,
        gross_rent=3000,
        loan_pmt_monthly=1200
    )
    
    # Verify both exist
    repairs = repair_svc.list_by_property(prop_id)
    rents = rent_svc.list_by_property(prop_id)
    
    assert len(repairs) > 0
    assert len(rents) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
