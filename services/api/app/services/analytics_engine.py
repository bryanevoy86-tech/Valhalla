"""
PACK AK: Analytics / Metrics Engine Service
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.holdings import Holding
from app.models.wholesale import WholesalePipeline
from app.models.dispo import DispoAssignment
from app.models.pro_retainer import Retainer
from app.models.pro_task_link import ProfessionalTaskLink
from app.models.children import ChildrenHub
from app.models.education_engine import Enrollment


def get_analytics_snapshot(db: Session) -> Dict[str, Any]:
    # Holdings
    holdings_q = db.query(Holding).filter(Holding.is_active.is_(True))
    holdings_count = holdings_q.count()
    total_value = sum(h.value_estimate or 0 for h in holdings_q)

    # Pipelines
    wholesale_total = db.query(WholesalePipeline).count()
    wholesale_under_contract = db.query(WholesalePipeline).filter(
        WholesalePipeline.stage == "under_contract"
    ).count()
    dispo_total = db.query(DispoAssignment).count()

    # Professionals
    retainers_total = db.query(Retainer).count()
    pro_tasks_total = db.query(ProfessionalTaskLink).count()

    # Children
    hubs_total = db.query(ChildrenHub).count()

    # Education
    enrollments_total = db.query(Enrollment).count()

    return {
        "holdings": {
            "active_count": holdings_count,
            "total_estimated_value": total_value,
        },
        "pipelines": {
            "wholesale_total": wholesale_total,
            "wholesale_under_contract": wholesale_under_contract,
            "dispo_assignments_total": dispo_total,
        },
        "professionals": {
            "retainers_total": retainers_total,
            "tasks_total": pro_tasks_total,
        },
        "children": {
            "hubs_total": hubs_total,
        },
        "education": {
            "enrollments_total": enrollments_total,
        },
    }
