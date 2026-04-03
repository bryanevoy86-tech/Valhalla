# Backend API Data Sanitization & Validation Guide

## Overview

This guide explains how to implement input sanitization and validation across your FastAPI backend to prevent malformed data issues and security vulnerabilities.

## Components

### 1. Core Sanitization Module (`core/sanitization.py`)

Provides HTML tag removal, field validation, and secure data processing functions.

#### Key Functions

#### `sanitize_input(input_value: Any) -> Any`
- Removes HTML tags from strings
- Decodes HTML entities
- Removes null bytes
- Returns non-string types unchanged

**Example:**
```python
from app.core.sanitization import sanitize_input

# Input: "<script>alert('xss')</script>Hello"
# Output: "Hello"
result = sanitize_input("<script>alert('xss')</script>Hello")
```

#### `validate_fields(fields: Dict, required_fields: List[str]) -> tuple[bool, Optional[str]]`
- Validates that required fields are present and non-empty
- Returns tuple of (is_valid, error_message)

**Example:**
```python
from app.core.sanitization import validate_fields

deal_data = {"title": "Nice Property", "notes": ""}
required = ["title", "notes"]

is_valid, error_msg = validate_fields(deal_data, required)
# Result: (False, "Field 'notes' is required and cannot be empty")
```

#### `sanitize_deal_data(deal_data: Dict) -> Dict`
- Sanitizes all string fields in a deal dictionary
- Preserves numeric and None values

**Example:**
```python
from app.core.sanitization import sanitize_deal_data

deal_data = {
    "title": "<p>Property</p>",
    "arv": 250000,
    "notes": None
}

sanitized = sanitize_deal_data(deal_data)
# Result: {"title": "Property", "arv": 250000, "notes": None}
```

#### `validate_deal_fields(deal_data: Dict) -> tuple[bool, Optional[str]]`
- Validates deal-specific rules (stage, numeric ranges, etc.)
- Checks for valid stage values
- Validates numeric fields (ARV: >= 0, score: 0-100)

#### `validate_numeric_field(value: Any, min_val: float, max_val: float) -> tuple[bool, Optional[str]]`
- Validates numeric fields with optional range checking
- Handles type conversion and validation

### 2. Error Logging Module (`core/error_logging.py`)

Provides structured error logging and standardized error responses.

#### Key Classes

#### `APIErrorLogger`

Static utility class for logging different error types:

```python
from app.core.error_logging import APIErrorLogger

# Log API request
APIErrorLogger.log_request_payload(
    endpoint="/deals",
    payload={"title": "Property", "arv": 250000},
    metadata={"user_id": 123}
)

# Log API error
try:
    # some_operation()
except Exception as err:
    APIErrorLogger.log_api_error(
        endpoint="/deals",
        error=err,
        payload={"title": "Property"},
        status_code=500
    )

# Log validation error
APIErrorLogger.log_validation_error(
    endpoint="/deals",
    field="title",
    error_message="Title cannot be empty",
    received_value=""
)

# Log sanitization
APIErrorLogger.log_sanitization(
    endpoint="/deals",
    field="notes",
    original="<script>alert('xss')</script>",
    sanitized=""
)
```

## Usage Examples

### Example 1: Basic Deal Creation with Sanitization

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.sanitization import sanitize_deal_data, validate_deal_fields
from app.core.error_logging import APIErrorLogger
from app.schemas.match import DealBriefIn, DealBriefOut
from app.models.match import DealBrief

router = APIRouter(prefix="/deals", tags=["deals"])

@router.post("", response_model=DealBriefOut)
def create_deal(payload: DealBriefIn, db: Session = Depends(get_db)):
    """Create a new deal with sanitization and validation."""
    try:
        # Convert to dict
        deal_dict = payload.model_dump()
        
        # Sanitize
        sanitized = sanitize_deal_data(deal_dict)
        
        # Validate
        is_valid, error_msg = validate_deal_fields(sanitized)
        if not is_valid:
            APIErrorLogger.log_validation_error(
                endpoint="/deals",
                field="deal_data",
                error_message=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid data", "message": error_msg}
            )
        
        # Create and save
        deal = DealBrief(**sanitized)
        db.add(deal)
        db.commit()
        db.refresh(deal)
        
        APIErrorLogger.log_request_payload(
            endpoint="/deals",
            payload=sanitized,
            metadata={"deal_id": deal.id, "status": "created"}
        )
        
        return deal
        
    except HTTPException:
        raise
    except Exception as err:
        APIErrorLogger.log_api_error(
            endpoint="/deals",
            error=err,
            payload=payload.model_dump(),
            status_code=500
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create deal", "message": str(err)}
        )
```

### Example 2: Custom Field Validation

```python
from app.core.sanitization import sanitize_input, validate_numeric_field

@router.patch("/{deal_id}", response_model=DealBriefOut)
def update_deal(deal_id: int, updates: dict, db: Session = Depends(get_db)):
    """Update a deal with custom validation."""
    
    deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Validate and sanitize title if provided
    if "title" in updates:
        sanitized_title = sanitize_input(updates["title"])
        if not sanitized_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty after sanitization"
            )
        deal.title = sanitized_title
    
    # Validate ARV if provided
    if "arv" in updates:
        is_valid, error_msg = validate_numeric_field(
            updates["arv"], 
            min_val=0, 
            max_val=10000000
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ARV: {error_msg}"
            )
        deal.arv = updates["arv"]
    
    # Sanitize notes
    if "notes" in updates:
        deal.notes = sanitize_input(updates["notes"])
    
    db.commit()
    db.refresh(deal)
    return deal
```

### Example 3: List Endpoint with Parameter Sanitization

```python
@router.get("", response_model=List[DealBriefOut])
def list_deals(
    status: str | None = None,
    region: str | None = None,
    db: Session = Depends(get_db)
):
    """List deals with parameter sanitization."""
    
    q = db.query(DealBrief)
    
    # Sanitize and filter by status
    if status:
        sanitized_status = sanitize_input(status)
        q = q.filter(DealBrief.status == sanitized_status)
    
    # Sanitize and filter by region
    if region:
        sanitized_region = sanitize_input(region)
        q = q.filter(DealBrief.region == sanitized_region)
    
    return q.order_by(DealBrief.id.desc()).limit(500).all()
```

## Logging Configuration

### Add to FastAPI Main App

```python
from fastapi import FastAPI
from app.core.error_logging import RequestLoggingMiddleware
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')
    ]
)

app = FastAPI()

# Add logging middleware
app.add_middleware(RequestLoggingMiddleware)
```

### Backend Logging Output

The system logs the following:

```
2024-03-15 10:30:45 - app.routers.deals - INFO - Creating deal with data: {'title': 'Property Sale', ...}
2024-03-15 10:30:45 - app.core.sanitization - INFO - Field sanitized: title | Original: '<p>Property</p>' | Sanitized: 'Property'
2024-03-15 10:30:46 - app.routers.deals - INFO - Deal created successfully with id: 42
```

## Validation Rules

### Deal Fields

| Field | Required | Type | Rules |
|-------|----------|------|-------|
| title | Yes | String | Non-empty after sanitization |
| stage | No | String | Must be: lead_received, prospect, negotiation, pending_close, closed, lost |
| arv | No | Float | Must be >= 0 |
| score | No | Float | Must be 0-100 |
| notes | No | String | HTML tags removed, can be empty |

### Custom Validation

To add custom validation rules for a field:

```python
from app.core.sanitization import sanitize_input

def validate_custom_field(field_value: str) -> tuple[bool, Optional[str]]:
    """Custom validation for a specific field."""
    
    # Sanitize first
    sanitized = sanitize_input(field_value)
    
    # Apply custom rules
    if len(sanitized) < 3:
        return False, "Field must be at least 3 characters"
    
    if len(sanitized) > 255:
        return False, "Field cannot exceed 255 characters"
    
    # Add more custom rules as needed
    
    return True, None
```

## Security Best Practices

1. **Always Sanitize User Input**: Use `sanitize_input()` for all string fields from request bodies
2. **Validate Before Saving**: Call validation functions before database operations
3. **Log Suspicious Activity**: Use `APIErrorLogger` to track potential attacks
4. **Type Checking**: Use Pydantic schemas for initial type validation
5. **Parametrized Queries**: Always use ORM or parametrized queries to prevent SQL injection
6. **Error Messages**: Don't expose sensitive information in error responses

## Testing

### Test Sanitization

```python
import pytest
from app.core.sanitization import sanitize_input, validate_deal_fields

def test_html_tag_removal():
    result = sanitize_input("<script>alert('xss')</script>Hello")
    assert result == "Hello"

def test_null_byte_removal():
    result = sanitize_input("Hello\x00World")
    assert result == "HelloWorld"

def test_validate_deal_required_fields():
    deal_data = {"title": ""}
    is_valid, error = validate_deal_fields(deal_data)
    assert not is_valid

def test_validate_deal_numeric_ranges():
    deal_data = {"title": "Property", "score": 150}
    is_valid, error = validate_deal_fields(deal_data)
    assert not is_valid  # score > 100
```

## Debugging

### Enable Detailed Logging

```python
import logging

# In your app startup
debug_logger = logging.getLogger('app.core.sanitization')
debug_logger.setLevel(logging.DEBUG)

debug_logger = logging.getLogger('app.core.error_logging')
debug_logger.setLevel(logging.DEBUG)
```

### Frontend Testing

Before submitting form, log the payload in WeWeb:

```javascript
console.log("Final Payload before submitting:", dealData);
// Check for:
// - HTML tags or scripts
// - Undefined or null values
// - Unexpected characters
```

## Migration Guide

If you have existing endpoints without sanitization:

1. Import sanitization utilities: `from app.core.sanitization import ...`
2. Add sanitization before validation
3. Add error handling with `APIErrorLogger`
4. Test thoroughly with malformed data
5. Deploy gradually to production

## Support

For issues or questions:
1. Check the logs in `api.log`
2. Review the validation rules in the table above
3. Run the test suite to verify sanitization functions
4. Contact the development team with specific error messages and payloads
