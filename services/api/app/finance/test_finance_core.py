"""
Tests for financial core engine
"""

from app.finance.deal_ledger import DealLedger
from app.finance.payment_intent import PaymentIntent
from app.finance.disbursement_engine import build_disbursement_plan


def test_deal_ledger_creation():
    """Verify deal ledger can be created with financial data."""
    ledger = DealLedger(
        deal_id="deal_001",
        purchase_price=500000.0,
        assignment_fee=15000.0,
        earnest_money=5000.0,
        closing_costs=2500.0,
    )
    
    assert ledger.deal_id == "deal_001"
    assert ledger.purchase_price == 500000.0
    assert ledger.assignment_fee == 15000.0
    assert ledger.to_dict()["deal_id"] == "deal_001"


def test_expected_profit_calculation():
    """Verify expected profit calculation: assignment_fee - closing_costs."""
    ledger = DealLedger(
        deal_id="deal_002",
        purchase_price=400000.0,
        assignment_fee=12000.0,
        closing_costs=2000.0,
    )
    
    expected = ledger.calculate_expected_profit()
    assert expected == 10000.0  # 12000 - 2000


def test_actual_profit_calculation():
    """Verify actual profit calculation: revenue - expenses."""
    ledger = DealLedger(
        deal_id="deal_003",
        purchase_price=300000.0,
        assignment_fee=10000.0,
        revenue=12000.0,
        expenses=2000.0,
    )
    
    actual = ledger.calculate_actual_profit()
    assert actual == 10000.0  # 12000 - 2000


def test_payment_intent_creation():
    """Verify payment intent can be created."""
    intent = PaymentIntent(
        deal_id="deal_004",
        payer="buyer",
        payee="seller",
        amount=500000.0,
        purpose="property_purchase",
    )
    
    assert intent.deal_id == "deal_004"
    assert intent.payer == "buyer"
    assert intent.payee == "seller"
    assert intent.status == "pending"


def test_payment_intent_approval():
    """Verify payment intent can be approved."""
    intent = PaymentIntent(
        deal_id="deal_005",
        payer="buyer",
        payee="seller",
        amount=500000.0,
        purpose="property_purchase",
    )
    
    assert intent.status == "pending"
    intent.approve()
    assert intent.status == "approved"


def test_disbursement_plan_generation():
    """Verify disbursement plan generates correct payment intents."""
    data = {
        "deal_id": "deal_006",
        "purchase_price": 500000.0,
        "assignment_fee": 15000.0,
        "earnest_money": 5000.0,
    }
    
    plan = build_disbursement_plan(data["deal_id"], data)
    
    assert len(plan) == 3  # earnest + purchase + assignment
    
    # Verify earnest money goes to title company
    earnest = next((p for p in plan if p.purpose == "earnest_money"), None)
    assert earnest is not None
    assert earnest.payee == "title_company"
    assert earnest.amount == 5000.0
    
    # Verify purchase price goes to seller
    purchase = next((p for p in plan if p.purpose == "property_purchase"), None)
    assert purchase is not None
    assert purchase.payee == "seller"
    assert purchase.amount == 500000.0
    
    # Verify assignment fee goes to Valhalla
    assignment = next((p for p in plan if p.purpose == "assignment_fee"), None)
    assert assignment is not None
    assert assignment.payee == "Valhalla Legacy Inc."
    assert assignment.amount == 15000.0
