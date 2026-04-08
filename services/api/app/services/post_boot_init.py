import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.seeds.community_seed import seed_community

log = logging.getLogger(__name__)

RUNTIME_DIR = Path("runtime")
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

INIT_STATE_FILE = RUNTIME_DIR / "post_boot_init_state.json"
INIT_LOCK_FILE = RUNTIME_DIR / "post_boot_init.lock"


def _write_state(status: str, detail: str | None = None) -> None:
    payload = {
        "status": status,
        "detail": detail,
        "updated_at": datetime.utcnow().isoformat(),
    }
    INIT_STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_init_state() -> dict:
    if not INIT_STATE_FILE.exists():
        return {
            "status": "not_started",
            "detail": None,
            "updated_at": None,
            "lock_present": INIT_LOCK_FILE.exists(),
        }

    try:
        payload = json.loads(INIT_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        payload = {
            "status": "unknown",
            "detail": "Could not parse init state file.",
            "updated_at": None,
        }

    payload["lock_present"] = INIT_LOCK_FILE.exists()
    return payload


def _community_tables_exist(db: Session) -> bool:
    inspector = inspect(db.bind)
    required = {
        "community_contacts",
        "community_campaigns",
        "community_interactions",
        "community_tasks",
        "community_referrals",
        "community_reputation_events",
    }
    existing = set(inspector.get_table_names())
    return required.issubset(existing)


def _community_seed_needed(db: Session) -> bool:
    from app.models.community import CommunityContact

    count = db.query(CommunityContact).count()
    return count == 0


def run_post_boot_init_sync() -> dict:
    if INIT_LOCK_FILE.exists():
        return {
            "ok": False,
            "status": "skipped",
            "detail": "Initialization already running.",
        }

    INIT_LOCK_FILE.write_text("running", encoding="utf-8")
    _write_state("running", "Post-boot initialization started.")

    db: Session = SessionLocal()
    try:
        if not _community_tables_exist(db):
            msg = "Community tables do not exist yet. Run migrations first."
            _write_state("waiting_for_migrations", msg)
            return {"ok": False, "status": "waiting_for_migrations", "detail": msg}

        if _community_seed_needed(db):
            seed_community(db)
            db.commit()
            msg = "Community seed completed."
            _write_state("completed", msg)
            return {"ok": True, "status": "completed", "detail": msg}

        msg = "Seed skipped. Community data already exists."
        _write_state("completed", msg)
        return {"ok": True, "status": "completed", "detail": msg}

    except Exception as e:
        db.rollback()
        msg = f"Post-boot init failed: {e}"
        log.exception(msg)
        _write_state("failed", msg)
        return {"ok": False, "status": "failed", "detail": msg}
    finally:
        db.close()
        if INIT_LOCK_FILE.exists():
            INIT_LOCK_FILE.unlink(missing_ok=True)


async def run_post_boot_init(delay_seconds: int = 5) -> dict:
    await asyncio.sleep(delay_seconds)
    return await asyncio.to_thread(run_post_boot_init_sync)
