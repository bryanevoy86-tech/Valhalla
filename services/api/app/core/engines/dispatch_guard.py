"""
Dispatch guards for SANDBOX enforcement.
Use in service-layer send/dispatch functions to prevent bypasses.
"""

from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.actions import OUTREACH, CONTRACT_SEND


def guard_outreach(engine_name: str = "wholesaling") -> None:
    """
    Call this immediately before ANY real-world outreach effect:
    - email, sms, calls
    - webhooks / external notifications
    - buyer blasts, dispo sends
    """
    enforce_engine(engine_name, OUTREACH)


def guard_contract_send(engine_name: str = "wholesaling") -> None:
    """
    Call this immediately before ANY send-for-signature / e-sign request.
    """
    enforce_engine(engine_name, CONTRACT_SEND)
