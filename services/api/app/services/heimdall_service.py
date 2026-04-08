"""
Heimdall v0.1 Service - Operator-Assist Deal Analysis & Stage Management
Heimdall analyzes deals, identifies blockers, recommends actions, and executes stage changes with approval.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.deal import Deal
from app.models.simple_contract import SimpleContract
from app.audit.service import log_event
from app.audit.schemas import AuditEventCreate


# ===== STAGE RULES =====

VALID_STAGE_TRANSITIONS = {
    "draft": ["lead_received"],
    "lead_received": ["preliminary_analysis"],
    "preliminary_analysis": ["offer_ready"],
    "offer_ready": ["under_contract"],
    "under_contract": ["closed"],
    "closed": [],  # terminal
}

STAGE_REQUIREMENTS = {
    "draft": [],
    "lead_received": [],
    "preliminary_analysis": ["arv", "repairs"],
    "offer_ready": ["offer_exists"],
    "under_contract": ["contract_exists", "contract_content_filled"],
    "closed": ["contract_signed"],
}


# ===== DATA CLASSES =====

class DealAnalysis:
    """Structured deal analysis result."""
    def __init__(
        self,
        deal_id: int,
        current_stage: str,
        deal_data: Dict[str, Any],
        offer_data: Optional[Dict[str, Any]],
        contract_data: Optional[Dict[str, Any]],
        buyer_match_data: Optional[Dict[str, Any]],
        missing_fields: List[str],
        blocker_flags: List[str],
        risk_flags: List[str],
        recommended_stage: Optional[str],
        recommendation_reason: str,
        can_advance: bool,
    ):
        self.deal_id = deal_id
        self.current_stage = current_stage
        self.deal_data = deal_data
        self.offer_data = offer_data
        self.contract_data = contract_data
        self.buyer_match_data = buyer_match_data
        self.missing_fields = missing_fields
        self.blocker_flags = blocker_flags
        self.risk_flags = risk_flags
        self.recommended_stage = recommended_stage
        self.recommendation_reason = recommendation_reason
        self.can_advance = can_advance
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "deal_id": self.deal_id,
            "analysis_timestamp": self.timestamp.isoformat() + "Z",
            "current_stage": self.current_stage,
            "deal_data": self.deal_data,
            "offer_data": self.offer_data,
            "contract_data": self.contract_data,
            "buyer_match_data": self.buyer_match_data,
            "missing_fields": self.missing_fields,
            "blocker_flags": self.blocker_flags,
            "risk_flags": self.risk_flags,
            "recommendations": {
                "next_valid_stages": VALID_STAGE_TRANSITIONS.get(self.current_stage, []),
                "recommended_stage": self.recommended_stage,
                "recommendation_reason": self.recommendation_reason,
                "can_advance_now": self.can_advance,
                "why_cannot_advance": None if self.can_advance else (
                    self.blocker_flags[0] if self.blocker_flags else "Unknown blocker"
                ),
            },
        }


# ===== HELPER FUNCTIONS =====

def _get_deal_context(deal_id: int, db: Session) -> tuple:
    """Load deal, offer, contract, buyer_match from database."""
    # Query canonical Deal model
    deal = db.query(Deal).filter(Deal.id == deal_id).first()

    if not deal:
        return None, None, None, None, None

    # Get offer (gracefully handle if table doesn't exist)
    offer = None
    try:
        from sqlalchemy import text
        # Query the offers table by deal_id
        offer_row = db.execute(
            text("SELECT id, deal_id, offer_price, status FROM offers WHERE deal_id = :deal_id LIMIT 1"),
            {"deal_id": deal_id}
        ).first()
        # Convert to simple object for compatibility
        if offer_row:
            class OfferData:
                def __init__(self, row):
                    self.id = row[0]
                    self.deal_id = row[1]
                    self.offer_price = row[2]
                    self.status = row[3]
            offer = OfferData(offer_row)
    except Exception:
        # offers table doesn't exist or model issue - skip
        pass

    # Get contract (gracefully handle if table doesn't exist)
    contract = None
    try:
        # Query the contracts table by deal_id
        contract_row = db.execute(
            text("SELECT id, deal_id, offer_id, status, content, signing_status, created_at, updated_at FROM contracts WHERE deal_id = :deal_id LIMIT 1"),
            {"deal_id": deal_id}
        ).first()
        # Convert to simple object for compatibility
        if contract_row:
            class ContractData:
                def __init__(self, row):
                    self.id = row[0]
                    self.deal_id = row[1]
                    self.offer_id = row[2]
                    self.status = row[3]
                    self.content = row[4]
                    self.signing_status = row[5]
                    self.created_at = row[6]
                    self.updated_at = row[7]
            contract = ContractData(contract_row)
    except Exception:
        # contracts table doesn't exist or model issue - skip
        pass

    # Get buyer match (gracefully handle if table doesn't exist)
    buyer_match_row = None
    try:
        from sqlalchemy import text
        buyer_match_row = db.execute(
            text("SELECT * FROM buyer_matches WHERE deal_id = ? ORDER BY created_at DESC LIMIT 1"),
            [deal_id]
        ).first()
    except Exception:
        # buyer_matches table doesn't exist - skip
        pass

    return deal, offer, contract, buyer_match_row, deal


def _build_deal_data_dict(deal: Any) -> Dict[str, Any]:
    """Extract deal data for analysis."""
    return {
        "id": deal.id,
        "status": getattr(deal, 'status', 'unknown'),
        "stage": getattr(deal, 'stage', None),
        "arv": float(getattr(deal, 'arv', 0) or 0),
        "estimated_repair_cost": float(getattr(deal, 'estimated_repair_cost', 0) or 0),
        "max_allowable_offer": float(getattr(deal, 'max_allowable_offer', 0) or 0),
        "score": float(getattr(deal, 'score', 0) or 0),
        "created_at": str(getattr(deal, 'created_at', 'N/A')),
        "title": getattr(deal, 'title', None),
    }


def _build_offer_data_dict(offer: Any) -> Optional[Dict[str, Any]]:
    """Extract offer data for analysis."""
    if not offer:
        return None
    return {
        "id": getattr(offer, 'id', None),
        "deal_id": getattr(offer, 'correlation_id', None),
        "recommended_offer": float(getattr(offer, 'recommended_offer', 0) or 0),
        "status": getattr(offer, 'status', 'unknown'),
    }


def _build_contract_data_dict(contract: Any) -> Optional[Dict[str, Any]]:
    """Extract contract data for analysis."""
    if not contract:
        return None
    return {
        "id": contract.id,
        "deal_id": contract.deal_id,
        "status": contract.status,
        "content_filled": bool(contract.content),
        "signing_status": contract.signing_status,
        "created_at": str(contract.created_at),
    }


def _build_buyer_match_dict(buyer_match_row: Any) -> Optional[Dict[str, Any]]:
    """Extract buyer match data for analysis."""
    if not buyer_match_row:
        return None
    return {
        "buyer_id": buyer_match_row[2],  # buyer_id is column 2
        "match_score": float(buyer_match_row[3] or 0),  # match_score column 3
        "status": buyer_match_row[5],  # status column 5
    }


def _detect_blockers(
    deal: Any,
    offer: Any,
    contract: Any,
    buyer_match: Any,
    current_stage: str,
) -> tuple:
    """Detect blocker and risk flags based on current stage."""
    blocker_flags = []
    risk_flags = []

    # Stage-specific blockers
    if current_stage == "preliminary_analysis":
        if not getattr(deal, 'arv', None):
            blocker_flags.append("missing_arv")
        if not getattr(deal, 'estimated_repair_cost', None):
            blocker_flags.append("missing_repair_cost")

    elif current_stage == "offer_ready":
        if not offer:
            blocker_flags.append("no_offer_created")

    elif current_stage == "under_contract":
        if not contract:
            blocker_flags.append("no_contract")
        elif not contract.content:
            blocker_flags.append("contract_content_empty")

    elif current_stage == "closed":
        if not contract or not contract.signing_status:
            blocker_flags.append("contract_not_signed")

    # Risk flags (always checked, non-blocking)
    if offer and deal:
        arv = float(getattr(deal, 'arv', 0) or 0)
        repairs = float(getattr(deal, 'estimated_repair_cost', 0) or 0)
        if arv > 0 and repairs / arv > 0.5:
            risk_flags.append(f"high_repair_ratio_{int(repairs/arv*100)}pct")

    if not buyer_match and current_stage in ["offer_ready", "under_contract"]:
        risk_flags.append("no_buyer_match")

    if not contract and current_stage in ["under_contract", "closed"]:
        risk_flags.append("no_contract_yet")

    return blocker_flags, risk_flags


def _recommend_next_stage(current_stage: str, blockers: List[str], deal: Any) -> tuple:
    """Recommend next stage based on current stage and blockers."""
    next_stages = VALID_STAGE_TRANSITIONS.get(current_stage, [])

    if not next_stages:
        return None, "No valid transitions from this stage"

    # Primary recommendation is first valid transition
    recommended = next_stages[0]

    # Reason
    if blockers:
        reason = f"Blockers prevent advancing: {', '.join(blockers[:2])}"
        can_advance_now = False
    else:
        reason = f"Ready to advance to {recommended}"
        can_advance_now = True

    return recommended if can_advance_now else None, reason


# ===== MAIN FUNCTIONS =====

def analyze_deal(deal_id: int, db: Session) -> DealAnalysis:
    """
    Analyze a deal and return structured recommendations.
    """
    deal, offer, contract, buyer_match_row, _ = _get_deal_context(deal_id, db)

    if not deal:
        raise ValueError(f"Deal {deal_id} not found")

    current_stage = getattr(deal, 'stage', 'draft')  # FIXED: Use 'stage' (pipeline), not 'status' (health)

    # Build data dicts
    deal_data = _build_deal_data_dict(deal)
    offer_data = _build_offer_data_dict(offer)
    contract_data = _build_contract_data_dict(contract)
    buyer_match_data = _build_buyer_match_dict(buyer_match_row)

    # Detect missing fields
    missing_fields = []
    if not deal_data.get('arv'):
        missing_fields.append("deal.arv")
    if not deal_data.get('estimated_repair_cost'):
        missing_fields.append("deal.estimated_repair_cost")
    if not offer_data and current_stage != "lead_received":
        missing_fields.append("offer")
    if not contract_data and current_stage in ["under_contract", "closed"]:
        missing_fields.append("contract")

    # Detect blockers and risks
    blocker_flags, risk_flags = _detect_blockers(deal, offer, contract, buyer_match_row, current_stage)

    # Recommend next stage
    recommended_stage, recommendation_reason = _recommend_next_stage(current_stage, blocker_flags, deal)
    can_advance = recommended_stage is not None

    return DealAnalysis(
        deal_id=deal_id,
        current_stage=current_stage,
        deal_data=deal_data,
        offer_data=offer_data,
        contract_data=contract_data,
        buyer_match_data=buyer_match_data,
        missing_fields=missing_fields,
        blocker_flags=blocker_flags,
        risk_flags=risk_flags,
        recommended_stage=recommended_stage,
        recommendation_reason=recommendation_reason,
        can_advance=can_advance,
    )


def advance_stage_with_approval(
    deal_id: int,
    requested_stage: str,
    approved_by: str,
    reason: str,
    override_reason: Optional[str] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Advance a deal to the requested stage, with explicit approval and audit logging.
    """
    if not db:
        raise ValueError("Database session required")

    deal, _, _, _, full_deal = _get_deal_context(deal_id, db)

    if not deal or not full_deal:
        raise ValueError(f"Deal {deal_id} not found")

    current_stage = getattr(deal, 'stage', 'draft')  # FIXED: Use 'stage' (pipeline), not 'status' (health)

    # Validate transition
    valid_next_stages = VALID_STAGE_TRANSITIONS.get(current_stage, [])
    if requested_stage not in valid_next_stages:
        # Log rejection
        try:
            log_event(db, AuditEventCreate(
                actor="Heimdall_v0.1",
                action="heimdall_stage_advance_rejected",
                target=f"deal_{deal_id}",
                entity_type="deal",
                entity_id=deal_id,
                result="rejected",
                meta={
                    "deal_id": deal_id,
                    "from_stage": current_stage,
                    "requested_stage": requested_stage,
                    "reason": f"Invalid transition from {current_stage} to {requested_stage}",
                    "approved_by": approved_by,
                }
            ))
        except Exception as e:
            print(f"Warning: Could not log rejection event: {e}")
        
        return {
            "deal_id": deal_id,
            "action": "stage_advance_rejected",
            "previous_stage": current_stage,
            "new_stage": None,
            "approved_by": None,
            "requested_stage": requested_stage,
            "result": "rejected",
            "reason": f"Invalid transition from {current_stage} to {requested_stage}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # Analyze for blockers
    analysis = analyze_deal(deal_id, db)

    # Check blockers
    if analysis.blocker_flags and not override_reason:
        # Log rejection
        try:
            log_event(db, AuditEventCreate(
                actor="Heimdall_v0.1",
                action="heimdall_stage_advance_rejected",
                target=f"deal_{deal_id}",
                entity_type="deal",
                entity_id=deal_id,
                result="rejected",
                meta={
                    "deal_id": deal_id,
                    "from_stage": current_stage,
                    "requested_stage": requested_stage,
                    "blockers": analysis.blocker_flags,
                    "reason": f"Blockers prevent advancement",
                    "approved_by": approved_by,
                }
            ))
        except Exception as e:
            print(f"Warning: Could not log blocker rejection event: {e}")
        
        return {
            "deal_id": deal_id,
            "action": "stage_advance_rejected",
            "previous_stage": current_stage,
            "new_stage": None,
            "approved_by": None,
            "requested_stage": requested_stage,
            "result": "rejected",
            "reason": f"Blockers prevent advancement: {', '.join(analysis.blocker_flags)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # Log analysis event
    try:
        log_event(db, AuditEventCreate(
            actor="Heimdall_v0.1",
            action="heimdall_analyzed_deal",
            target=f"deal_{deal_id}",
            entity_type="deal",
            entity_id=deal_id,
            result="success",
            meta={
                "deal_id": deal_id,
                "current_stage": current_stage,
                "recommended_stage": analysis.recommended_stage,
                "blockers": analysis.blocker_flags,
                "risks": analysis.risk_flags,
            }
        ))
    except Exception as e:
        print(f"Warning: Could not log analysis event: {e}")

    # Log recommendation event
    try:
        log_event(db, AuditEventCreate(
            actor="Heimdall_v0.1",
            action="heimdall_recommended_stage",
            target=f"deal_{deal_id}",
            entity_type="deal",
            entity_id=deal_id,
            result="success",
            meta={
                "deal_id": deal_id,
                "from_stage": current_stage,
                "to_stage": requested_stage,
                "reason": reason,
                "override_used": bool(override_reason),
            }
        ))
    except Exception as e:
        print(f"Warning: Could not log recommendation event: {e}")

    # Perform stage advancement
    full_deal.stage = requested_stage  # FIXED: Write to 'stage' (pipeline), not 'status' (health)
    db.commit()
    db.refresh(full_deal)

    # Log advancement event
    try:
        log_event(db, AuditEventCreate(
            actor="Heimdall_v0.1",
            action="heimdall_stage_advanced",
            target=f"deal_{deal_id}",
            entity_type="deal",
            entity_id=deal_id,
            result="success",
            meta={
                "deal_id": deal_id,
                "from_stage": current_stage,
                "to_stage": requested_stage,
                "approved_by": approved_by,
                "reason": reason,
                "override_used": bool(override_reason),
                "override_reason": override_reason or None,
            }
        ))
    except Exception as e:
        print(f"Warning: Could not log advancement event: {e}")

    return {
        "deal_id": deal_id,
        "action": "stage_advanced",
        "previous_stage": current_stage,
        "new_stage": requested_stage,
        "approved_by": approved_by,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "result": "success",
        "notes": "Stage advanced successfully",
        "blocker_overrides": [override_reason] if override_reason else [],
    }


# ===== TASK MANAGEMENT =====

import json
from pathlib import Path

TASKS_FILE = Path("var/heimdall_tasks.json")
OUTCOMES_FILE = Path("var/heimdall_outcomes.json")


def _ensure_var_dir() -> None:
    """Ensure var directory exists."""
    Path("var").mkdir(exist_ok=True)


def create_task(contact_id: int, action: str, priority: str = "medium") -> Dict[str, Any]:
    """Create a new task for Heimdall to track."""
    _ensure_var_dir()
    
    # Load existing tasks
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            tasks = json.load(f)
    else:
        tasks = []
    
    # Generate new task ID
    task_id = max([t.get("id", 0) for t in tasks], default=0) + 1
    
    # Create task
    task = {
        "id": task_id,
        "contact_id": contact_id,
        "action": action,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    
    tasks.append(task)
    
    # Save
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)
    
    return task


def get_pending_tasks() -> List[Dict[str, Any]]:
    """Get all pending tasks sorted by priority."""
    _ensure_var_dir()
    
    if not TASKS_FILE.exists():
        return []
    
    with open(TASKS_FILE) as f:
        all_tasks = json.load(f)
    
    # Filter pending tasks and sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    pending = [t for t in all_tasks if t.get("status") == "pending"]
    
    return sorted(
        pending,
        key=lambda t: priority_order.get(t.get("priority", "medium"), 99)
    )


def record_outcome(contact_id: int, result: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Record the outcome of an action on a contact."""
    _ensure_var_dir()
    
    # Load existing outcomes
    if OUTCOMES_FILE.exists():
        with open(OUTCOMES_FILE) as f:
            outcomes = json.load(f)
    else:
        outcomes = []
    
    # Generate new outcome ID
    outcome_id = max([o.get("id", 0) for o in outcomes], default=0) + 1
    
    # Create outcome
    outcome = {
        "id": outcome_id,
        "contact_id": contact_id,
        "result": result,
        "notes": notes,
        "recorded_at": datetime.utcnow().isoformat() + "Z",
    }
    
    outcomes.append(outcome)
    
    # Save
    with open(OUTCOMES_FILE, "w") as f:
        json.dump(outcomes, f, indent=2)
    
    return outcome
