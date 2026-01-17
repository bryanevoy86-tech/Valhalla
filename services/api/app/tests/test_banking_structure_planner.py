"""
PACK SC: Banking & Accounts Structure Planner Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base, get_db
from app.main import app
from app.models.banking_structure_planner import (
    BankAccountPlan,
    AccountSetupChecklist,
    AccountIncomeMapping,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_account_plan():
    """Test creating a bank account plan."""
    response = client.post(
        "/banking/accounts",
        json={
            "account_id": "acc_001",
            "name": "Operations Account",
            "category": "operations",
            "purpose": "Daily business revenue and expenses",
            "institution": "Chase",
            "status": "planned",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == "acc_001"
    assert data["category"] == "operations"


def test_get_account_plan():
    """Test retrieving an account plan."""
    client.post(
        "/banking/accounts",
        json={
            "account_id": "acc_002",
            "name": "Tax Reserve",
            "category": "tax_reserve",
            "purpose": "Hold quarterly tax deposits",
        },
    )
    response = client.get("/banking/accounts/acc_002")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tax Reserve"


def test_list_accounts():
    """Test listing all account plans."""
    client.post(
        "/banking/accounts",
        json={
            "account_id": "acc_003",
            "name": "Fun Funds Account",
            "category": "fun_funds",
            "purpose": "Discretionary spending",
        },
    )
    response = client.get("/banking/accounts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_accounts_by_category():
    """Test filtering accounts by category."""
    client.post(
        "/banking/accounts",
        json={
            "account_id": "acc_004",
            "name": "Emergency Buffer",
            "category": "emergency",
            "purpose": "Emergency reserves",
        },
    )
    response = client.get("/banking/accounts/category/emergency")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(a["category"] == "emergency" for a in data)


def test_update_account_status():
    """Test updating account status."""
    account_response = client.post(
        "/banking/accounts",
        json={
            "account_id": "acc_005",
            "name": "Payroll Account",
            "category": "payroll",
            "purpose": "Pay employees",
        },
    )

    response = client.patch("/banking/accounts/acc_005/status?status=open")
    assert response.status_code == 200
    data = response.json()
    assert data["new_status"] == "open"


def test_create_income_mapping():
    """Test creating an income routing rule."""
    # Create an account first
    client.post(
        "/banking/accounts",
        json={
            "account_id": "acc_006",
            "name": "Operations",
            "category": "operations",
            "purpose": "Main operations",
        },
    )

    response = client.post(
        "/banking/mappings",
        json={
            "target_account_id": 1,
            "source_type": "income_source",
            "source_name": "Client Payments",
            "percentage": 100.0,
            "is_active": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_name"] == "Client Payments"


def test_get_active_mappings():
    """Test retrieving all active routing rules."""
    response = client.get("/banking/mappings")
    assert response.status_code == 200
    data = response.json()
    # Response may be empty if no mappings exist yet
    assert isinstance(data, list)


def test_get_account_summary():
    """Test getting banking structure summary."""
    response = client.get("/banking/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_accounts" in data
    assert "accounts_by_category" in data
    assert "total_mappings" in data
    assert "active_mappings" in data


def test_create_setup_checklist():
    """Test creating a setup checklist item."""
    # Create account first
    account_response = client.post(
        "/banking/accounts",
        json={
            "account_id": "acc_007",
            "name": "Setup Test",
            "category": "operations",
            "purpose": "Test account",
        },
    )
    account_id = account_response.json()["id"]

    response = client.post(
        "/banking/setup-checklist",
        json={
            "account_plan_id": account_id,
            "step_name": "Gather identification documents",
            "documents_required": ["passport", "utility_bill"],
            "is_completed": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["step_name"] == "Gather identification documents"


def test_full_banking_workflow():
    """Test a complete banking structure setup."""
    # Create operations account
    ops_response = client.post(
        "/banking/accounts",
        json={
            "account_id": "ops_001",
            "name": "Operations",
            "category": "operations",
            "purpose": "Revenue and expenses",
            "status": "planned",
        },
    )
    assert ops_response.status_code == 200

    # Create tax reserve account
    tax_response = client.post(
        "/banking/accounts",
        json={
            "account_id": "tax_001",
            "name": "Tax Reserve",
            "category": "tax_reserve",
            "purpose": "Tax holding",
            "status": "planned",
        },
    )
    assert tax_response.status_code == 200

    # Get summary
    summary_response = client.get("/banking/summary")
    data = summary_response.json()
    assert data["total_accounts"] == 2
