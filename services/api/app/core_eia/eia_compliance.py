def validate_eia_compliance(payload):
    """
    Validate that payload contains all required EIA compliance fields.
    
    Expected fields:
    - income_summary
    - expense_summary
    - receipt_index
    - bank_checklist
    """
    missing_fields = ["income_summary", "expense_summary", "receipt_index", "bank_checklist"]
    missing = [field for field in missing_fields if field not in payload]
    return {
        "compliant": len(missing) == 0,
        "missing_fields": missing,
        "status": "EIA Report Ready" if len(missing) == 0 else "EIA Report Incomplete"
    }
