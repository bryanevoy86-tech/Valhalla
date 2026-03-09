from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Path, status

from app.routers.governance_king import KING_POLICY
from app.routers.governance_queen import QUEEN_POLICY
from app.routers.governance_odin import ODIN_POLICY
from app.routers.governance_loki import LOKI_POLICY
from app.routers.governance_tyr import TYR_POLICY
from app.schemas.governance import (
    GovernancePolicies,
    KingPolicy,
    QueenPolicy,
    OdinPolicy,
    LokiPolicy,
    TyrPolicy,
)

router = APIRouter(
    prefix="/governance",
    tags=["Governance", "Policy"],
)

# Map a short god name to the in-memory policy object and its type
_POLICY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "king": {"obj": KING_POLICY, "type": KingPolicy},
    "queen": {"obj": QUEEN_POLICY, "type": QueenPolicy},
    "odin": {"obj": ODIN_POLICY, "type": OdinPolicy},
    "loki": {"obj": LOKI_POLICY, "type": LokiPolicy},
    "tyr": {"obj": TYR_POLICY, "type": TyrPolicy},
}


@router.get(
    "/policies",
    response_model=GovernancePolicies,
    status_code=status.HTTP_200_OK,
    summary="Get current governance policies for all gods",
    description="Returns the full in-memory configuration for King, Queen, Odin, Loki, and Tyr.",
)
def get_policies() -> GovernancePolicies:
    return GovernancePolicies(
        king=KING_POLICY,
        queen=QUEEN_POLICY,
        odin=ODIN_POLICY,
        loki=LOKI_POLICY,
        tyr=TYR_POLICY,
    )


@router.get(
    "/policies/{god}",
    status_code=status.HTTP_200_OK,
    summary="Get policy for a specific god",
    description="Returns the current in-memory policy for the specified god.",
)
def get_policy_for_god(
    god: str = Path(..., description="One of: king, queen, odin, loki, tyr"),
):
    god = god.lower()
    entry = _POLICY_REGISTRY.get(god)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown god '{god}'. Allowed: {list(_POLICY_REGISTRY.keys())}",
        )

    return entry["obj"]


@router.patch(
    "/policies/{god}",
    status_code=status.HTTP_200_OK,
    summary="Patch/update policy for a specific god",
    description=(
        "Accepts a partial JSON body and applies it to the given god's policy. "
        "This updates the in-memory configuration only (no database). "
        "Careful: changes persist only for the life of the process."
    ),
)
def update_policy_for_god(
    god: str = Path(..., description="One of: king, queen, odin, loki, tyr"),
    patch: Dict[str, Any] = None,
):
    god = god.lower()
    entry = _POLICY_REGISTRY.get(god)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown god '{god}'. Allowed: {list(_POLICY_REGISTRY.keys())}",
        )

    if patch is None:
        patch = {}

    policy_obj = entry["obj"]
    policy_type = entry["type"]

    # Convert existing policy to dict, apply patch, then validate
    current_data = policy_obj.model_dump()
    merged = {**current_data, **patch}

    try:
        updated_policy = policy_type.model_validate(merged)
    except Exception as exc:  # pydantic.ValidationError or others
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid policy patch for {god}: {exc}",
        )

    # Update the in-memory object in-place
    policy_obj.__dict__.update(updated_policy.__dict__)

    return policy_obj
