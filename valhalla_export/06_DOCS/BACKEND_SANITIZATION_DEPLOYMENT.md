# Backend API Sanitization - Implementation Checklist

## ✅ Completed

### Core Infrastructure
- [x] Created `core/sanitization.py` with utility functions:
  - `sanitize_input()` - HTML tag removal, entity decoding, null byte removal
  - `sanitize_string_field()` - String field sanitization with defaults
  - `validate_fields()` - Required field validation
  - `validate_numeric_field()` - Numeric range validation
  - `sanitize_deal_data()` - Deal-specific sanitization
  - `validate_deal_fields()` - Deal-specific validation

- [x] Created `core/error_logging.py` with structured logging:
  - `APIErrorLogger` class for standardized error logging
  - `RequestLoggingMiddleware` for request/response tracking
  - `create_error_response()` for consistent error formatting

### Routers Updated
- [x] Updated `routers/deals.py`:
  - Integrated sanitization in `add_deal()` POST endpoint
  - Added validation before database insert
  - Added comprehensive error logging
  - Sanitized status parameter in `list_deals()` GET endpoint

- [x] Updated `leads/service.py`:
  - Created `sanitize_lead_data()` function
  - Created `validate_lead_data()` function with comprehensive checks
  - Updated `create_lead()` with sanitization and validation
  - Added error logging throughout service layer
  - Updated `get_leads_by_status()` with status sanitization
  - Updated `update_lead_status()` with validation

- [x] Updated `leads/router.py`:
  - Added error handling for validation failures
  - Integrated APIErrorLogger for API errors
  - Added proper HTTP status codes
  - Added try-catch blocks with logging

### Documentation
- [x] Created `BACKEND_SANITIZATION_GUIDE.md` with:
  - Component overview
  - Function documentation with examples
  - Usage examples for different endpoint types
  - Validation rules reference table
  - Security best practices
  - Testing examples
  - Debugging guide

## 📋 Next Steps - Deploy Across Codebase

### 1. Add Logging Middleware to Main App (HIGH PRIORITY)

```python
# In services/api/app/main.py
from app.core.error_logging import RequestLoggingMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log')
    ]
)

# Add middleware after app creation
app.add_middleware(RequestLoggingMiddleware)
```

### 2. Update Other Deal-Related Routers

Routers to update with similar sanitization pattern:
- [ ] `routers/deal_analyzer.py` - Add sanitization to deal analysis endpoints
- [ ] `routers/deal_finalization.py` - Add sanitization to finalization endpoints
- [ ] `routers/deal_lifecycle.py` - Add sanitization to lifecycle endpoints
- [ ] `routers/deal_workflow_status.py` - Add sanitization to status endpoints

Template for each route:
```python
from app.core.sanitization import sanitize_input, sanitize_deal_data, validate_deal_fields
from app.core.error_logging import APIErrorLogger

@router.post("/{deal_id}/action")
async def perform_action(deal_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        # Sanitize
        sanitized = sanitize_deal_data(payload)
        
        # Validate
        is_valid, error_msg = validate_deal_fields(sanitized)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Process
        # ... your logic here ...
        
    except Exception as e:
        APIErrorLogger.log_api_error(endpoint="...", error=e, payload=payload)
        raise HTTPException(status_code=500, detail="Operation failed")
```

### 3. Update Other Create/Update Endpoints

Routers with create/update operations that should be secured:
- [ ] `routers/intake.py` - Sanitize intake form data
- [ ] `routers/buyers.py` - Sanitize buyer information
- [ ] `routers/contracts.py` - Sanitize contract data
- [ ] `routers/negotiations.py` - Sanitize negotiation data
- [ ] `routers/offers.py` - Sanitize offer data

### 4. Implement Frontend Logging (WeWeb)

Add to form submission handlers:

```javascript
// Before API call
console.log("Final Payload before submitting:", payload);

// After API response
response
  .then(result => {
    console.log("API Success Response:", result);
  })
  .catch(err => {
    console.error("API Error: ", err);
    console.error("Error Response:", err.response?.data);
  });
```

### 5. Add Request Logging to App Startup

```python
# In services/api/app/main.py startup event
@app.on_event("startup")
async def startup():
    logging.info("API Server starting up...")
    logging.info("Sanitization and validation systems enabled")
    
@app.on_event("shutdown")
async def shutdown():
    logging.info("API Server shutting down")
```

### 6. Test Sanitization & Validation

Run these tests before full deployment:

```bash
# Test the sanitization module
pytest tests/test_sanitization.py -v

# Test the deal endpoint
pytest tests/test_deals_endpoint.py -v

# Test the leads endpoint
pytest tests/test_leads_endpoint.py -v
```

Example test file:
```python
# tests/test_sanitization.py
import pytest
from app.core.sanitization import sanitize_input, validate_deal_fields

def test_sanitize_html_tags():
    result = sanitize_input("<script>alert('xss')</script>")
    assert "<script>" not in result
    assert "alert" in result  # Text content preserved

def test_validate_required_fields():
    deal = {"title": "", "arv": 100000}
    is_valid, error = validate_deal_fields(deal)
    assert not is_valid
    assert "required" in error.lower()

def test_validate_numeric_range():
    deal = {"title": "Property", "score": 150}
    is_valid, error = validate_deal_fields(deal)
    assert not is_valid  # Score > 100
```

### 7. Monitor Logs

Track in api.log for:
```
✅ SUCCESS PATTERNS:
- "Deal created successfully with id:"
- "Lead created successfully with id:"
- "API Request: endpoint=/..."

⚠️ WARNING PATTERNS TO INVESTIGATE:
- "Validation failed:"
- "Field sanitized:" (check if it's expected)
- "Invalid data received:" (possible bad client)

❌ ERROR PATTERNS REQUIRING ACTION:
- "Failed to create deal:"
- "Failed to create lead:"
- "API Error:" (unexpected exceptions)
```

### 8. Gradual Rollout Strategy

1. **Phase 1** (NOW):
   - Deploy updated `deals.py` and `leads/*` files
   - Monitor logs for validation errors
   - Verify frontend still works

2. **Phase 2** (Week 1):
   - Update remaining deal-related routers
   - Run integration tests
   - Check WeWeb logs for issues

3. **Phase 3** (Week 2):
   - Update all create/update endpoints
   - Full system testing
   - Performance verification

4. **Phase 4** (Week 3):
   - Enable strict validation mode
   - Document any edge cases found

## 🔍 Validation Rules Reference

### Deal Fields
| Field | Required | Sanitization | Validation |
|-------|----------|---------------|------------|
| title | Yes | HTML removal | Non-empty after sanitization |
| headline | Yes | HTML removal | Non-empty after sanitization |
| stage | No | Input sanitization | Must be in allowed list |
| status | No | Input sanitization | Must be: active, inactive, archived |
| arv | No | None (numeric) | >= 0 |
| score | No | None (numeric) | 0-100 |
| notes | No | HTML removal | Can be empty |
| region | No | Input sanitization | Max 255 chars |

### Lead Fields
| Field | Required | Sanitization | Validation |
|-------|----------|---------------|------------|
| lead_name | Yes | HTML removal | 2-255 chars |
| lead_email | Yes | None (Pydantic) | Valid email |
| lead_phone | Yes | Input sanitization | >= 10 chars |
| lead_status | Yes | Input sanitization | Must be in allowed list |
| source | Yes | Input sanitization | 1-255 chars |
| property_address | No | HTML removal | Can be empty |
| estimated_arv | No | None (numeric) | >= 0 |
| notes | No | HTML removal | Can be empty |

## 🚀 Commands to Deploy

```bash
# From workspace root

# 1. Run tests
python -m pytest services/api/app/tests/ -v

# 2. Format code
black services/api/

# 3. Check for issues
ruff check services/api/

# 4. Type check
mypy services/api/app/core/sanitization.py

# 5. Start server with logging
python -m uvicorn services.api.app.main:app --reload --log-level info
```

## 📊 Monitoring Dashboard

Key metrics to track:
- **Sanitization Rate**: % of requests with sanitized fields (high = expected)
- **Validation Failure Rate**: % of requests rejected by validation (should be < 5%)
- **Error Rate**: % of requests resulting in 500 errors (should be < 1%)
- **Response Time**: API latency (should remain < 200ms)

Add to logs:
```python
import time

@router.post("/deals")
async def create_deal(...):
    start_time = time.time()
    try:
        # ... processing ...
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Request completed in {elapsed:.2f}s")
```

## 🆘 Troubleshooting

### Issue: "Field becomes empty after sanitization"
- **Cause**: Input contains only HTML tags or special characters
- **Solution**: Update validation error message or pre-validate in frontend

### Issue: "Invalid numeric value"
- **Cause**: ARV or score not properly formatted in JSON
- **Solution**: Ensure frontend sends numbers, not strings

### Issue: High validation failure rate
- **Cause**: Frontend not sanitizing before sending
- **Solution**: Add sanitization to frontend form submission

### Issue: Logs growing too large
- **Solution**: Configure log rotation:
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'api.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
```

---

## Summary

**What's Now Enabled:**
- ✅ HTML tag removal from string inputs
- ✅ Required field validation
- ✅ Numeric range checking
- ✅ Deal-specific validation rules
- ✅ Lead-specific validation rules
- ✅ Structured error logging
- ✅ Request/response tracking
- ✅ Sanitization audit trail

**Next Immediate Actions:**
1. Add logging middleware to main app
2. Deploy and monitor deals/leads endpoints
3. Update remaining deal routers
4. Test with malformed data
5. Monitor error logs for issues

**Long-term:**
- Extend pattern to all create/update endpoints
- Implement rate limiting
- Add request signing/verification
- Consider API versioning strategy
