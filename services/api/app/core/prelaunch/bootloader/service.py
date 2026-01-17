"""PACK-CORE-PRELAUNCH-01: Bootloader - Service"""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from . import models


def run_boot_sequence(db: Session) -> models.BootLog:
    steps: List[dict] = []

    def add_step(name: str, status: str, message: str | None = None):
        steps.append({"name": name, "status": status, "message": message})

    # TODO: wire in real checks
    add_step("Load Bryan Profile", "SUCCESS")
    add_step("Load Safeguards", "SUCCESS")
    add_step("Check Core Services", "SUCCESS")
    add_step("Run Risk Snapshot", "SUCCESS")
    add_step("Run System Health", "SUCCESS")

    log = models.BootLog(
        run_at=datetime.utcnow(),
        status="SUCCESS",
        steps=steps,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_last_boot(db: Session) -> models.BootLog | None:
    return db.query(models.BootLog).order_by(models.BootLog.run_at.desc()).first()
