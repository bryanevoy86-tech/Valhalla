from __future__ import annotations

import random
from typing import Any

CANADA_CITIES = [
    ("BC","Vancouver"), ("BC","Surrey"), ("BC","Kelowna"),
    ("AB","Calgary"), ("AB","Edmonton"),
    ("MB","Winnipeg"),
    ("SK","Regina"), ("SK","Saskatoon"),
    ("ON","Toronto"), ("ON","Mississauga"), ("ON","Ottawa"), ("ON","Hamilton"),
    ("QC","Montreal"), ("QC","Quebec City"),
    ("NS","Halifax"),
]

USA_CITIES = [
    ("FL","Orlando"), ("FL","Tampa"), ("FL","Jacksonville"), ("FL","Miami"),
    ("TX","Dallas"), ("TX","Houston"), ("GA","Atlanta"),
    ("NC","Charlotte"), ("SC","Charleston"),
]

SELLER_REASONS = [
    "inherited", "tired_landlord", "job_loss", "divorce", "downsizing",
    "vacant", "tax_pressure", "hoarder", "repairs_too_much", "moving",
]

STAGES = ["new", "contacted", "qualified", "offer_sent", "negotiating"]
STRATEGIES = ["wholesale", "brrrr", "flip", "rental"]
PROPERTY_TYPES = ["sfh", "duplex", "triplex", "fourplex", "townhouse", "condo", "small_mf"]

def _rand_money(lo: int, hi: int) -> float:
    return float(random.randint(lo, hi))

def _pick_country_mix(country: str) -> tuple[str, str, str]:
    if country == "CA":
        prov, city = random.choice(CANADA_CITIES)
        return "CA", prov, city
    prov, city = random.choice(USA_CITIES)
    return "US", prov, city

def generate_seed_deal(country: str) -> dict[str, Any]:
    ctry, prov, city = _pick_country_mix(country)
    strategy = random.choice(STRATEGIES)
    ptype = random.choice(PROPERTY_TYPES)

    # broad ranges (intentionally wide; you'll tune later)
    if ctry == "CA":
        arv = _rand_money(220_000, 950_000)
        asking = arv * random.uniform(0.55, 0.95)
        repairs = _rand_money(10_000, 140_000)
        rent = _rand_money(1200, 4200)
    else:
        arv = _rand_money(150_000, 800_000)
        asking = arv * random.uniform(0.55, 0.92)
        repairs = _rand_money(8_000, 120_000)
        rent = _rand_money(1100, 4500)

    motivation = random.choices(["high","medium","low"], weights=[45,40,15])[0]
    stage = random.choices(STAGES, weights=[35,25,20,10,10])[0]
    timeline = random.choice([7, 14, 21, 30, 45, 60, 90])

    # crude MAO heuristic (placeholder; scoring pack will compute better)
    mao = max(0.0, (arv * 0.70) - repairs)

    return {
        "country": ctry,
        "province_state": prov,
        "city": city,
        "address": None,
        "postal_zip": None,
        "strategy": strategy,
        "property_type": ptype,
        "bedrooms": random.choice([2,3,3,4,4,5]),
        "bathrooms": random.choice([1,1.5,2,2.5,3]),
        "sqft": random.choice([850, 1000, 1200, 1400, 1600, 2000, 2400]),
        "arv": round(arv, 2),
        "asking_price": round(asking, 2),
        "est_repairs": round(repairs, 2),
        "mao": round(mao, 2),
        "est_rent_monthly": float(rent) if strategy in ("brrrr","rental") else None,
        "seller_motivation": motivation,
        "seller_reason": random.choice(SELLER_REASONS),
        "timeline_days": timeline,
        "stage": stage,
        "lead_source": "seed",
        "tags": [strategy, ctry.lower(), prov.lower()],
        "notes": "Seed deal for training/scoring. Not a real lead.",
        "meta": {"seed": True},
    }

def generate_seed_batch(n: int = 200, ca_ratio: float = 0.5) -> list[dict[str, Any]]:
    out = []
    for _ in range(n):
        country = "CA" if random.random() < ca_ratio else "US"
        out.append(generate_seed_deal(country))
    return out
