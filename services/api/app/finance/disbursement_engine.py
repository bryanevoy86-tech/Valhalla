from __future__ import annotations

from typing import List
from app.finance.payment_intent import PaymentIntent


def build_disbursement_plan(deal_id: str, data: dict) -> List[PaymentIntent]:
    intents = []

    if data.get("earnest_money"):
        intents.append(
            PaymentIntent(
                deal_id=deal_id,
                payer="buyer",
                payee="title_company",
                amount=float(data["earnest_money"]),
                purpose="earnest_money"
            )
        )

    if data.get("purchase_price"):
        intents.append(
            PaymentIntent(
                deal_id=deal_id,
                payer="buyer",
                payee="seller",
                amount=float(data["purchase_price"]),
                purpose="property_purchase"
            )
        )

    if data.get("assignment_fee"):
        intents.append(
            PaymentIntent(
                deal_id=deal_id,
                payer="buyer",
                payee="Valhalla Legacy Inc.",
                amount=float(data["assignment_fee"]),
                purpose="assignment_fee"
            )
        )

    return intents
