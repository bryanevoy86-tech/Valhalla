from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.services.csv_property_parser_service import parse_property_csv
from app.heimdall.services.bulk_property_enrichment_service import (
    bulk_create_property_intel_records,
)


def run_csv_bulk_property_enrichment(
    db: Session,
    csv_text: str,
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    End-to-end CSV upload → property intel records workflow.

    Steps:
    1. Parse CSV rows, validate, normalize, convert types
    2. If no valid records found, return early
    3. Batch create all valid records in property intel database
    4. Return parse summary + creation results

    Args:
        db: SQLAlchemy session
        csv_text: Raw CSV content as string
        created_by: Audit trail user identifier

    Returns:
        {
            "status": "CSV_BULK_PROPERTY_ENRICHMENT_COMPLETE" | "NO_VALID_RECORDS",
            "parsed": {"parsed_count": int, "failed_count": int, "failed": []},
            "created": {"created_count": int, "failed_count": int, "created": [], "failed": []}
        }
    """

    parsed = parse_property_csv(csv_text)

    if parsed.get("parsed_count", 0) == 0:
        return {
            "status": "NO_VALID_RECORDS",
            "parsed": parsed,
            "created": None,
        }

    created = bulk_create_property_intel_records(
        db=db,
        records=parsed.get("records", []),
        created_by=created_by,
    )

    return {
        "status": "CSV_BULK_PROPERTY_ENRICHMENT_COMPLETE",
        "parsed": {
            "parsed_count": parsed.get("parsed_count"),
            "failed_count": parsed.get("failed_count"),
            "failed": parsed.get("failed"),
        },
        "created": created,
    }
