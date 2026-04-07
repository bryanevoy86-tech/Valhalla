from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = BASE_DIR / "legal_contacts.json"


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {
            "defaults": {
                "lawyer_email": "",
                "accountant_email": "",
                "title_company": "",
                "title_company_email": "",
                "cc": []
            },
            "companies": {}
        }
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def get_registry() -> dict[str, Any]:
    return _load_registry()


def save_registry(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _merge_contact_layers(*layers: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "lawyer_email": "",
        "accountant_email": "",
        "title_company": "",
        "title_company_email": "",
        "cc": []
    }

    for layer in layers:
        if not layer:
            continue
        for key in ("lawyer_email", "accountant_email", "title_company", "title_company_email"):
            value = layer.get(key)
            if value:
                merged[key] = value

        cc_values = layer.get("cc", [])
        if cc_values:
            existing = set(merged["cc"])
            for item in cc_values:
                if item and item not in existing:
                    merged["cc"].append(item)
                    existing.add(item)

    return merged


def resolve_legal_contacts(
    company_name: str | None = None,
    region_code: str | None = None,
    deal_type: str | None = None,
) -> dict[str, Any]:
    registry = _load_registry()

    global_defaults = registry.get("defaults", {})
    company = registry.get("companies", {}).get(company_name or "", {})
    company_defaults = company.get("defaults", {})
    region_defaults = company.get("regions", {}).get(region_code or "", {})
    deal_type_defaults = company.get("deal_types", {}).get(deal_type or "", {})

    merged = _merge_contact_layers(
        global_defaults,
        company_defaults,
        region_defaults,
        deal_type_defaults,
    )

    recipients: list[str] = []
    if merged.get("lawyer_email"):
        recipients.append(merged["lawyer_email"])
    if merged.get("title_company_email"):
        recipients.append(merged["title_company_email"])

    return {
        "company_name": company_name,
        "region_code": region_code,
        "deal_type": deal_type,
        "lawyer_email": merged.get("lawyer_email", ""),
        "accountant_email": merged.get("accountant_email", ""),
        "title_company": merged.get("title_company", ""),
        "title_company_email": merged.get("title_company_email", ""),
        "cc": merged.get("cc", []),
        "recipients": recipients,
    }


def update_company_region_contacts(
    company_name: str,
    region_code: str,
    lawyer_email: str = "",
    accountant_email: str = "",
    title_company: str = "",
    title_company_email: str = "",
    cc: list[str] | None = None,
) -> dict[str, Any]:
    cc = cc or []
    data = _load_registry()

    companies = data.setdefault("companies", {})
    company = companies.setdefault(company_name, {})
    regions = company.setdefault("regions", {})
    regions[region_code] = {
        "lawyer_email": lawyer_email,
        "accountant_email": accountant_email,
        "title_company": title_company,
        "title_company_email": title_company_email,
        "cc": cc,
    }

    save_registry(data)
    return regions[region_code]
