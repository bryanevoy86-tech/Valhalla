# Input Sanitization & Validation for POST /api/deals

## Overview
Comprehensive input sanitization and validation has been added to the **POST /api/deals** endpoint to prevent security vulnerabilities and ensure data quality.

## Security Features Implemented

### 1. **XSS (Cross-Site Scripting) Prevention**
- Removes all HTML and XML tags from string inputs
- Strips JavaScript protocol handlers (`javascript:`)
- Removes event handler attributes (`onclick`, `onload`, `onerror`, etc.)
- Sanitizes both `title` and `notes` fields

**Example:**
```python
Input:  '<script>alert("XSS")</script>Sample Property'
Output: 'Sample Property'
```

### 2. **SQL Injection Prevention**
- Input is handled as data, not code (Pydantic validation)
- Parameterized queries used throughout service layer
- No dynamic query construction from user input

**Example:**
```python
Input:  "'; DROP TABLE deals; --"
Output: "''; DROP TABLE deals; --" (treated as literal string)
```

### 3. **Type Validation & Coercion**
Validates that numeric fields contain valid numbers within reasonable bounds:

- **ARV** (After-Repair Value): Non-negative decimal, max $1 quadrillion
- **Repair Cost**: Non-negative decimal
- **Max Allowable Offer**: Non-negative decimal
- **Assignment Fee**: Non-negative decimal
- **Score**: 0-100 range (capped at boundaries)

**Example:**
```python
Input:  {arv: -250000, score: 250}
Output: {arv: 0, score: 100}
```

### 4. **Choice Field Validation**
Validates that enumerated fields only contain allowed values:

- **Stage**: lead_received, intake_review, underwrite_ready, offer_ready, offer_sent, contract_pending, contract_signed, buyer_matching, dispo_ready, closed, dead
- **Status**: active, on_hold, archived
- **Disposition Status**: pending, matched, expired, withdrawn, dead, null

Invalid values default to the safe default (`lead_received`, `active`, `pending`)

**Example:**
```python
Input:  {stage: "invalid_xyz"}
Output: {stage: "lead_received"}
```

### 5. **Whitespace Normalization**
- Trims leading/trailing whitespace from all string fields
- Prevents bypass attacks using whitespace padding

## Implementation Files

### [validation.py](services/api/app/deals/validation.py) - Sanitization Functions

```python
# Core sanitization functions:
sanitize_string(input)           # Remove HTML/XSS, trim whitespace
sanitize_numeric(input, default) # Validate and convert to Decimal
sanitize_choice(input, allowed, default)  # Validate against allowed list
validate_deal_data(data)         # Complete validation pipeline
```

### [router.py](services/api/app/deals/router.py) - Endpoint Integration

```python
@router.post("", response_model=DealOut)
async def create_deal_direct(deal: DealCreateDirect, db: Session = Depends(get_db)):
    # 1. Convert Pydantic model to dict
    deal_dict = deal.dict()
    
    # 2. Call validate_deal_data() to sanitize
    sanitized_data = validate_deal_data(deal_dict)
    
    # 3. Reconstruct model with clean data
    sanitized_deal = DealCreateDirect(**sanitized_data)
    
    # 4. Proceed to create deal
    db_deal = deal_service.create_deal_direct(db, sanitized_deal)
    
    return db_deal
```

## API Usage Examples

### Safe Input (passes through unchanged):
```bash
curl -X POST http://localhost:4000/api/deals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Property",
    "stage": "lead_received",
    "status": "active",
    "arv": 250000,
    "score": 85,
    "notes": "Clean notes"
  }'
```

### Malicious Input (gets sanitized):
```bash
curl -X POST http://localhost:4000/api/deals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "<script>alert(\"XSS\")</script>Property",
    "stage": "invalid_stage",
    "arv": -250000,
    "score": 250,
    "notes": "'; DROP TABLE deals; --"
  }'
```

**Response:**
```json
{
  "title": "Property",
  "stage": "lead_received",
  "arv": "0",
  "score": "100",
  "notes": "'; DROP TABLE deals; --"
}
```

## Testing

### Run Sanitization Tests:
```bash
cd d:\dev
python test_input_sanitization.py
```

This will test:
- ✅ XSS injections (HTML/script tags)
- ✅ SQL injection attempts
- ✅ JavaScript event handlers
- ✅ Negative number handling
- ✅ Out-of-range scores
- ✅ Invalid stage values
- ✅ Valid data passthrough

## Security Best Practices Applied

| Threat | Mitigation | Status |
|--------|-----------|--------|
| XSS Injection | HTML tag removal + event handler stripping | ✅ Implemented |
| SQL Injection | Parameterized queries + input validation | ✅ Implemented |
| Type Confusion | Strict type validation with Decimal/int | ✅ Implemented |
| Invalid State | Enum validation with safe defaults | ✅ Implemented |
| Negative Values | Min/max bounds on financial fields | ✅ Implemented |
| Whitespace Bypass | Input trimming | ✅ Implemented |
| Large Numbers | Bounds checking (±1e15) | ✅ Implemented |

## Error Handling

If validation fails, the endpoint returns:
- **400 Bad Request**: If lead_id doesn't exist
- **422 Unprocessable Entity**: If data cannot be processed
- **500 Internal Server Error**: Database/service errors

## Audit Trail

Each deal creation includes audit logging noting that "input was sanitized":
```json
{
  "action": "created",
  "notes": "Deal created directly via API (input sanitized)",
  "created_at": "2026-04-01T12:34:56"
}
```

## Performance Impact

- Minimal: All sanitization is O(n) where n = string length
- Typically <1ms per request
- No database queries for validation
- Character-level operations only
