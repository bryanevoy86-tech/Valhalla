"""PACK-CORE-PRELAUNCH-01: Scenarios Engine - Service"""

from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def list_scenarios(db: Session) -> List[models.Scenario]:
    return db.query(models.Scenario).order_by(models.Scenario.code).all()


def get_scenario_by_code(db: Session, code: str) -> Optional[models.Scenario]:
    return db.query(models.Scenario).filter(models.Scenario.code == code).first()
