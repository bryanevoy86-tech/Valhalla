from app.core.data_intake.quarantine_store import QuarantineStore
from app.core.data_intake.models import IntakeItem
from app.core.engines.errors import EngineBlocked

store = QuarantineStore()


def promote_to_clean(
    item_id: str,
    trust_tier: str = "T1",
):
    item = store.get(item_id)
    if not item:
        raise EngineBlocked("Item not found")

    if item.status != "QUARANTINE":
        raise EngineBlocked("Item is not in QUARANTINE")

    item.status = "CLEAN"
    item.trust_tier = trust_tier
    store.upsert(item)
    return item
