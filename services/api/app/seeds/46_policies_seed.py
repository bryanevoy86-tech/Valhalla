import os
from sqlalchemy.orm import Session
from app.policies.models import ClonePolicy, MirrorPolicy


def run(db: Session):
    if not db.query(ClonePolicy).first():
        db.add(
            ClonePolicy(
                enabled=True,
                min_days_between=int(os.getenv("CLONE_MIN_DAYS_BETWEEN", "7")),
                max_active=int(os.getenv("CLONE_MAX_ACTIVE", "12")),
                required_uptime_pct=float(os.getenv("CLONE_REQUIRED_UPTIME_PCT", "98.5")),
                required_cash_reserves=float(os.getenv("CLONE_REQUIRED_CASH_RESERVES", "25000")),
                required_net_margin_pct=float(os.getenv("CLONE_REQUIRED_NET_MARGIN_PCT", "18")),
                required_audit_score=float(os.getenv("CLONE_REQUIRED_AUDIT_SCORE", "90")),
                max_error_rate_ppm=int(os.getenv("CLONE_ERROR_RATE_MAX_PPM", "250")),
            )
        )
    if not db.query(MirrorPolicy).first():
        db.add(
            MirrorPolicy(
                enabled=True,
                min_days_between=int(os.getenv("MIRROR_MIN_DAYS_BETWEEN", "14")),
                max_active=int(os.getenv("MIRROR_MAX_ACTIVE", "2")),
                required_p90_rps=float(os.getenv("MIRROR_REQUIRED_TRAFFIC_P90_RPS", "5")),
                required_p95_latency_ms=float(os.getenv("MIRROR_REQUIRED_LATENCY_P95_MS", "350")),
            )
        )
    db.commit()
