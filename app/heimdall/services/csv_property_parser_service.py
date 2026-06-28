import csv
import io
from typing import Any, Dict, List

REQUIRED_ADDRESS_FIELDS = ["address", "city"]


def parse_property_csv(csv_text: str) -> Dict[str, Any]:
    """
    Parse property CSV and convert to bulk enrichment format.
    
    Required columns: address, city
    Optional columns: province_or_state, country, visible_distress_observed,
                      vacant_or_boarded, ownership_unverified, notes, photo_url,
                      estimated_arv, property_condition, vacant_or_occupied
    
    Steps:
    1. Parse CSV rows
    2. Normalize column names (lowercase, trim)
    3. Validate required fields (address, city)
    4. Build address_payload and property_data objects
    5. Return parsed records + failures
    """

    reader = csv.DictReader(io.StringIO(csv_text))
    records: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []

    for index, row in enumerate(reader, start=1):
        # Normalize column names: lowercase + trim values
        normalized = {
            key.strip().lower(): value.strip() if isinstance(value, str) else value
            for key, value in row.items()
            if key
        }

        # Validate required fields
        missing = [
            field
            for field in REQUIRED_ADDRESS_FIELDS
            if not normalized.get(field)
        ]

        if missing:
            failed.append(
                {
                    "row": index,
                    "reason": f"Missing required fields: {missing}",
                    "data": normalized,
                }
            )
            continue

        # Build address payload
        address_payload = {
            "address": normalized.get("address"),
            "city": normalized.get("city"),
            "province_or_state": normalized.get("province_or_state")
            or normalized.get("province")
            or normalized.get("state"),
            "country": normalized.get("country", "Canada"),
        }

        # Build property data (convert yes/true/1 to boolean)
        property_data = {
            "visible_distress_observed": normalized.get(
                "visible_distress_observed", ""
            ).lower()
            in ["true", "yes", "1"],
            "vacant_or_boarded": normalized.get("vacant_or_boarded", "").lower()
            in ["true", "yes", "1"],
            "ownership_unverified": normalized.get("ownership_unverified", "true").lower()
            in ["true", "yes", "1"],
            "notes": normalized.get("notes"),
            "photo_url": normalized.get("photo_url"),
            "estimated_arv": normalized.get("estimated_arv"),
            "property_condition": normalized.get("property_condition", "unknown"),
            "vacant_or_occupied": normalized.get("vacant_or_occupied", "unknown"),
        }

        records.append(
            {
                "address": address_payload,
                "property_data": property_data,
            }
        )

    return {
        "parsed_count": len(records),
        "failed_count": len(failed),
        "records": records,
        "failed": failed,
    }
