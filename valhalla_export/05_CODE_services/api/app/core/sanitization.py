"""
Input sanitization and validation utilities for API endpoints.
Provides HTML tag removal, field validation, and secure data processing.
"""

import re
import logging
from typing import Any, Dict, Optional, List
from html import escape, unescape

logger = logging.getLogger(__name__)


def sanitize_input(input_value: Any) -> Any:
    """
    Sanitize input by removing HTML tags and dangerous characters.
    
    Args:
        input_value: The input to sanitize (string, number, None, etc.)
    
    Returns:
        The sanitized input preserving original type where appropriate
    """
    if isinstance(input_value, str):
        # Remove HTML tags - matches <...> patterns
        sanitized = re.sub(r'<[^>]*>', '', input_value)
        # Remove dangerous URI protocols
        sanitized = re.sub(r'(?i)javascript:', '', sanitized)
        sanitized = re.sub(r'(?i)data:', '', sanitized)
        sanitized = re.sub(r'(?i)vbscript:', '', sanitized)
        # Decode any HTML entities
        sanitized = unescape(sanitized)
        # Remove any null bytes
        sanitized = sanitized.replace('\x00', '')
        return sanitized.strip()
    
    # Return non-string types unchanged
    return input_value


def sanitize_string_field(field_value: Optional[str], default: str = "") -> str:
    """
    Sanitize a string field with a default fallback.
    
    Args:
        field_value: The field value to sanitize
        default: Default value if field is None or empty
    
    Returns:
        Sanitized string value
    """
    if field_value is None or field_value == "":
        return default
    return sanitize_input(field_value)


def validate_fields(fields: Dict[str, Any], required_fields: Optional[List[str]] = None) -> tuple[bool, Optional[str]]:
    """
    Validate that required fields are present and non-empty.
    
    Args:
        fields: Dictionary of fields to validate
        required_fields: List of field names that must be present and non-empty.
                        If None, all fields are checked.
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    fields_to_check = required_fields if required_fields else list(fields.keys())
    
    for key in fields_to_check:
        field_value = fields.get(key)
        
        # Check if field exists and is not None, null, or empty string
        if field_value is None or field_value == "" or (isinstance(field_value, str) and not field_value.strip()):
            logger.error(f"Validation failed: Field '{key}' is invalid: {field_value}")
            return False, f"Field '{key}' is required and cannot be empty"
        
        # For string fields, ensure they have content after sanitization
        if isinstance(field_value, str):
            sanitized = sanitize_input(field_value)
            if not sanitized:
                logger.error(f"Validation failed: Field '{key}' is empty after sanitization")
                return False, f"Field '{key}' becomes empty after sanitization"
    
    return True, None


def validate_numeric_field(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> tuple[bool, Optional[str]]:
    """
    Validate numeric field with optional range checking.
    
    Args:
        value: The numeric value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        if value is None:
            return False, "Numeric field cannot be None"
        
        num_value = float(value)
        
        if min_val is not None and num_value < min_val:
            return False, f"Value must be >= {min_val}, got {num_value}"
        
        if max_val is not None and num_value > max_val:
            return False, f"Value must be <= {max_val}, got {num_value}"
        
        return True, None
    except (TypeError, ValueError) as e:
        return False, f"Invalid numeric value: {str(e)}"


def sanitize_deal_data(deal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize all fields in a deal data dictionary.
    
    Args:
        deal_data: Dictionary containing deal data
    
    Returns:
        Dictionary with sanitized values
    """
    sanitized_data = {}
    
    for key, value in deal_data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitize_input(value)
        elif value is None:
            sanitized_data[key] = value
        else:
            # Numbers and other types pass through
            sanitized_data[key] = value
    
    return sanitized_data


def validate_deal_fields(deal_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate deal data with deal-specific rules.
    
    Args:
        deal_data: Dictionary containing deal data
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    # Example deal field validation
    required_deal_fields = ["title"]  # Adjust based on your actual requirements
    
    # First, check required fields
    is_valid, error_msg = validate_fields(deal_data, required_deal_fields)
    if not is_valid:
        return False, error_msg
    
    # Validate numeric fields if present
    if "arv" in deal_data and deal_data["arv"] is not None:
        is_valid, error_msg = validate_numeric_field(deal_data["arv"], min_val=0)
        if not is_valid:
            return False, f"Invalid ARV: {error_msg}"
    
    if "score" in deal_data and deal_data["score"] is not None:
        is_valid, error_msg = validate_numeric_field(deal_data["score"], min_val=0, max_val=100)
        if not is_valid:
            return False, f"Invalid score: {error_msg}"
    
    # Validate stage if present
    if "stage" in deal_data and isinstance(deal_data["stage"], str):
        valid_stages = ["lead_received", "prospect", "negotiation", "pending_close", "closed", "lost"]
        if deal_data["stage"] not in valid_stages:
            return False, f"Invalid stage: {deal_data['stage']}. Must be one of {valid_stages}"
    
    return True, None


def log_sanitization_details(original_data: Dict[str, Any], sanitized_data: Dict[str, Any]) -> None:
    """
    Log details about sanitization for debugging purposes.
    
    Args:
        original_data: Original unsanitized data
        sanitized_data: Sanitized data
    """
    for key in original_data.keys():
        if original_data.get(key) != sanitized_data.get(key):
            logger.info(
                f"Field sanitized: {key} | "
                f"Original: {repr(original_data.get(key))} | "
                f"Sanitized: {repr(sanitized_data.get(key))}"
            )
