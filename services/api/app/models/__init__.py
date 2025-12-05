# Models module - Import all models here to ensure proper initialization order

# Core professional models
from app.models.pro_scorecard import Professional, InteractionLog, Scorecard

# Agreement models
from app.models.pro_retainer import Retainer

# Workflow models
from app.models.pro_task_link import ProfessionalTaskLink

# Contract models (old template model still exists for legacy support)
from app.models.contracts import ContractTemplate
# New PACK N Contract Record
from app.models.contract_record import ContractRecord

# Document tracking
from app.models.document_route import DocumentRoute

# Audit models
from app.models.audit_event import AuditEvent

# Governance models
from app.models.governance_decision import GovernanceDecision

__all__ = [
    "Professional",
    "InteractionLog",
    "Scorecard",
    "Retainer",
    "ProfessionalTaskLink",
    "ContractTemplate",
    "ContractRecord",
    "DocumentRoute",
    "AuditEvent",
    "GovernanceDecision",
]
