# services/api/app/routers/closing_playbook.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.routers.flow_prepare_closing import get_closing_context
from app.schemas.closing_context import ClosingContext

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "ClosingPlaybook"],
    dependencies=[Depends(require_prime_control_key)],
)


def _build_script(context: ClosingContext) -> Dict[str, Any]:
    """
    Build a structured playbook the closer (or Heimdall) can follow.
    """
    lead = context.lead
    deal = context.deal
    freeze = context.freeze
    uw = context.underwriting

    price_str = f"${deal.price:,}" if deal.price is not None else "the price"
    arv_str = f"${deal.arv:,}" if deal.arv is not None else "the after-repair value"
    region = deal.region or "your area"

    script: Dict[str, Any] = {}

    # Opening
    script["opening"] = context.suggested_opening

    # Rapport phase
    script["rapport_questions"] = [
        f"Hey {lead.name}, how have things been at the property on {lead.address or 'the place'}?",
        "What's got you thinking about making a move right now?",
        "If everything went perfectly for you with this sale, what would that look like?",
    ]

    # Discovery / pain
    script["diagnostic_questions"] = [
        "What's the biggest headache with the property for you right now?",
        "Have you already had other offers or conversations with agents/investors?",
        "How quickly do you ideally need this to be wrapped up?",
    ]

    # Numbers framing
    framing_lines: List[str] = []
    if uw.ltv is not None:
        framing_lines.append(
            f"Right now, at the numbers we're looking at, we're around {uw.ltv:.1%} "
            f"of what we think the property is worth after repairs."
        )
    if uw.equity_percent_of_arv is not None:
        framing_lines.append(
            f"That leaves roughly {uw.equity_percent_of_arv:.1%} of the value as "
            f"room for repairs, risk, and profit so the deal still makes sense."
        )
    if not framing_lines:
        framing_lines.append(
            "I want to walk through the numbers with you so we both see the same story "
            "on price, repairs, and what makes the deal work."
        )

    script["numbers_framing"] = framing_lines

    # Offer framing
    script["offer_framing"] = [
        f"If we can make {price_str} work, with us handling the repairs and hassle, "
        f"is that something that would put you in a good spot?",
        "On a scale of 1–10, where 10 means you're ready to sign today, where are you right now?",
    ]

    # Objection handling
    script["objection_prompts"] = [
        "What would need to change in this offer to make it a no-brainer for you?",
        "Sounds like the number is the main thing holding you back — is that fair?",
        "If we could tighten up the timeline or terms instead of the price, would that help?",
    ]

    # Closing prompts
    if freeze.has_freeze:
        script["closing_prompts"] = [
            "Given there are some risk flags on our side with the numbers, "
            "I want to be transparent and make sure this still feels fair to you.",
            "If we could agree on this today, are you comfortable moving forward so we "
            "can start the paperwork?",
        ]
    else:
        script["closing_prompts"] = [
            "If this all sounds good, are you comfortable moving forward today so we can lock this in?",
            "Would you like to move ahead with this and let us take the stress of the property off your plate?",
        ]

    # Summary line for Heimdall
    script["summary_for_ai"] = (
        f"Closing context for a {deal.property_type or 'property'} in {region} with "
        f"headline '{deal.headline or ''}'. Lead {lead.name} appears motivated due to "
        f"{lead.tags or 'general reasons'}. Use the script sections to guide the call, "
        "but adapt based on real-time responses."
    )

    return script


@router.get(
    "/closing_playbook/{backend_deal_id}",
    status_code=status.HTTP_200_OK,
    summary="Generate a closing playbook for a deal",
    description=(
        "Builds a closing playbook (script sections) for a given backend Deal. "
        "This is what Heimdall or the closer engine can follow in a live call."
    ),
)
def get_closing_playbook(
    backend_deal_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    context = get_closing_context(backend_deal_id, db)
    script = _build_script(context)

    return {
        "context": context,
        "script": script,
    }
