"""
Input validation and sanitization utilities for deals.

Provides sanitization functions to prevent XSS, injection attacks,
and ensure data quality.
"""
import re
from decimal import Decimal
from typing import Optional, Any, Dict


def sanitize_string(input_val: Any) -> str:
    """
    Sanitize string input by removing HTML tags and scripts.
    
    Args:
        input_val: Input value to sanitize
        
    Returns:
        str: Sanitized string, or empty string if not a string
    """
    if input_val is None:
        return ""
    
    if not isinstance(input_val, str):
        return str(input_val).strip()
    
    # Remove HTML/XML tags
    sanitized = re.sub(r'<\/?[^>]+(>|$)', "", input_val)
    
    # Remove script-like patterns
    sanitized = re.sub(r'javascript:', "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', "", sanitized, flags=re.IGNORECASE)
    
    # Strip whitespace
    return sanitized.strip()


def sanitize_numeric(input_val: Any, default: float = 0) -> Decimal:
    """
    Sanitize and convert input to Decimal (safe for currency).
    
    Args:
        input_val: Input value to convert
        default: Default value if conversion fails
        
    Returns:
        Decimal: Numeric value or default
    """
    if input_val is None:
        return Decimal(str(default))
    
    try:
        # Try to convert to float first, then Decimal for precision
        if isinstance(input_val, (int, float)):
            return Decimal(str(input_val))
        elif isinstance(input_val, Decimal):
            return input_val
        else:
            # Parse string representation
            parsed = float(input_val)
            # Validate it's a reasonable number (not infinity/NaN)
            if not (-1e15 < parsed < 1e15):
                return Decimal(str(default))
            return Decimal(str(parsed))
    except (ValueError, TypeError, OverflowError):
        return Decimal(str(default))


def sanitize_choice(input_val: Any, allowed: list, default: str) -> str:
    """
    Sanitize and validate choice from allowed list.
    
    Args:
        input_val: Input value to validate
        allowed: List of allowed values
        default: Default value if not in allowed list
        
    Returns:
        str: Validated choice or default
    """
    if input_val is None:
        return default
    
    sanitized = sanitize_string(input_val)
    
    if sanitized in allowed:
        return sanitized
    
    return default


def validate_deal_data(data: dict) -> Dict[str, Any]:
    """
    Validate and sanitize complete deal data dictionary.
    
    Args:
        data: Raw deal data from request
        
    Returns:
        dict: Validated and sanitized deal data
    """
    # Define allowed stages and statuses
    allowed_stages = [
        "lead_received", "intake_review", "underwrite_ready",
        "offer_ready", "offer_sent", "contract_pending",
        "contract_signed", "buyer_matching", "dispo_ready",
        "closed", "dead"
    ]
    
    allowed_statuses = ["active", "on_hold", "archived"]
    
    allowed_dispositions = [
        "pending", "matched", "expired", "withdrawn", 
        "dead", None
    ]
    
    # Sanitize string fields
    sanitized: Dict[str, Any] = {
        "title": sanitize_string(data.get("title", "Untitled Deal")),
        "notes": sanitize_string(data.get("notes", "")),
    }
    
    # Validate choice fields
    sanitized["stage"] = sanitize_choice(
        data.get("stage"), allowed_stages, "lead_received"
    )
    
    sanitized["status"] = sanitize_choice(
        data.get("status"), allowed_statuses, "active"
    )
    
    sanitized["disposition_status"] = sanitize_choice(
        data.get("disposition_status"), allowed_dispositions, "pending"
    )
    
    # Sanitize numeric fields (ensure non-negative for financial data)
    sanitized["arv"] = max(Decimal(0), sanitize_numeric(data.get("arv", 0)))
    sanitized["estimated_repair_cost"] = max(
        Decimal(0), sanitize_numeric(data.get("estimated_repair_cost", 0))
    )
    sanitized["max_allowable_offer"] = max(
        Decimal(0), sanitize_numeric(data.get("max_allowable_offer", 0))
    )
    sanitized["target_assignment_fee"] = max(
        Decimal(0), sanitize_numeric(data.get("target_assignment_fee", 0))
    )
    
    # Score must be between 0-100
    score_val = sanitize_numeric(data.get("score", 0))
    sanitized["score"] = min(Decimal(100), max(Decimal(0), score_val))
    
    # Pass through optional lead_id if provided
    if "lead_id" in data and data["lead_id"] is not None:
        try:
            sanitized["lead_id"] = int(data["lead_id"])
            if sanitized["lead_id"] <= 0:
                sanitized["lead_id"] = None
        except (ValueError, TypeError):
            sanitized["lead_id"] = None
    else:
        sanitized["lead_id"] = None
    
    return sanitized
