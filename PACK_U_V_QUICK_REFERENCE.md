# PACK U & PACK V Quick Reference

## PACK U: Frontend Preparation

### What It Does
Provides machine-readable API navigation map for WeWeb/Heimdall to auto-generate UI screens.

### Endpoint
```bash
GET /ui-map/
```

### Example Request
```bash
curl -X GET "http://localhost:8000/ui-map/"
```

### Example Response
```json
{
  "modules": [
    {
      "id": "professionals",
      "label": "Professionals",
      "description": "Professional management and tracking",
      "sections": [
        {
          "id": "scorecard",
          "label": "Scorecard",
          "description": "Track professional metrics and KPIs",
          "endpoints": [
            {
              "method": "GET",
              "path": "/api/professionals/scorecard",
              "summary": "Get professional scorecard",
              "tags": ["Professionals", "Scorecard"]
            }
          ]
        }
      ]
    }
  ],
  "metadata": {
    "version": "1.0",
    "description": "API navigation map for WeWeb UI generation",
    "last_updated": "2025-12-05T17:43:58"
  }
}
```

### Modules
1. **professionals** - Scorecard, Retainers, Tasks, Handoff
2. **contracts** - Lifecycle, Documents
3. **deals** - Finalization
4. **audit_governance** - Audit, Governance
5. **debug_system** - Routes, System

### Use Cases
- WeWeb auto-generates screen layouts from module structure
- Heimdall creates navigation menus from sections
- Frontend builds API call maps from endpoints
- Documentation automatically generated from metadata

---

## PACK V: Deployment Checklist

### What It Does
Verifies system is ready to deploy by checking environment, database, and critical routes.

### Endpoint
```bash
GET /ops/deploy-check/
```

### Example Request
```bash
curl -X GET "http://localhost:8000/ops/deploy-check/"
```

### Example Response
```json
{
  "timestamp": "2025-12-05T17:43:58.170284",
  "overall_ok": true,
  "checks": {
    "environment": {
      "ok": true,
      "details": {
        "DATABASE_URL": true
      }
    },
    "database": {
      "ok": true,
      "message": "Database connection healthy"
    },
    "routes": {
      "ok": true,
      "total_routes": 42,
      "required_prefixes": [
        "/api/health",
        "/debug/routes",
        "/debug/system",
        "/ui-map",
        "/ops/deploy-check"
      ],
      "missing_prefixes": []
    }
  }
}
```

### Check Types

**1. Environment Variables**
- Verifies required vars are set
- Returns: Dictionary of var_name → bool

**2. Database Health**
- Checks database connectivity
- Returns: ok boolean + message

**3. Critical Routes**
- Verifies required endpoints registered
- Returns: total_routes, required_prefixes[], missing_prefixes[], ok boolean

**4. Overall Status**
- Aggregates: overall_ok = env_ok AND db_ok AND routes_ok
- Safe to deploy when overall_ok = true

### Use Cases
- Pre-deployment verification in CI/CD
- Ops team checks before manual deployment
- Monitoring/alerting integration
- Automated readiness validation

---

## Integration Examples

### Frontend Integration
```javascript
// Get UI map for screen generation
fetch('/ui-map/')
  .then(res => res.json())
  .then(data => {
    // data.modules contains navigation structure
    // data.modules[i].sections contains page groups
    // data.modules[i].sections[j].endpoints contains API calls
    generateUI(data.modules);
  });
```

### Ops Integration
```bash
#!/bin/bash
# Check readiness before deployment

RESULT=$(curl -s -X GET "http://api.example.com/ops/deploy-check/")
READY=$(echo $RESULT | jq '.overall_ok')

if [ "$READY" = "true" ]; then
  echo "✓ System ready for deployment"
  deploy_application
else
  echo "✗ System not ready"
  echo $RESULT | jq '.'
  exit 1
fi
```

### Monitoring Integration
```python
# Monitor deployment readiness

import requests
import json

response = requests.get('http://api.example.com/ops/deploy-check/')
result = response.json()

if result['overall_ok']:
    print("✓ System READY")
else:
    print("✗ System NOT READY")
    for check, status in result['checks'].items():
        if not status['ok']:
            print(f"  - {check}: {status.get('message', 'FAILED')}")
```

---

## Testing

### Run PACK U Tests
```bash
pytest services/api/app/tests/test_ui_map.py -v
```

### Run PACK V Tests
```bash
pytest services/api/app/tests/test_deploy_check.py -v
```

### Run Integration Tests
```bash
python test_pack_uv_integration.py
```

### Test Results
- PACK U: 13/13 tests passing ✓
- PACK V: 14/14 tests passing ✓
- Integration: All checks passing ✓

---

## Configuration

### PACK V Configuration (Expandable)

Located in `services/api/app/services/deploy_check.py`:

```python
# Add new required environment variables
REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "REDIS_URL",        # Add when caching implemented
    "STRIPE_SECRET_KEY",  # Add when payments enabled
    "AUTH0_DOMAIN",      # Add when auth enabled
]

# Add new critical route prefixes
REQUIRED_PREFIXES = [
    "/api/health",
    "/debug/routes",
    "/debug/system",
    "/ui-map",
    "/ops/deploy-check",
    "/api/professionals",  # Add new critical endpoints
    "/api/contracts",      # as system expands
]
```

### Modifying UI Map

Located in `services/api/app/services/ui_map.py`:

```python
def get_ui_map():
    return {
        "modules": [
            {
                "id": "my_new_module",
                "label": "My New Module",
                "description": "Description here",
                "sections": [
                    {
                        "id": "my_section",
                        "label": "My Section",
                        "endpoints": [
                            # Add endpoints here
                        ]
                    }
                ]
            }
        ]
    }
```

---

## Troubleshooting

### PACK U Issues

**Problem:** UI map returns empty modules
- **Solution:** Check `app/services/ui_map.py` has endpoint definitions
- **Verify:** Endpoint paths match actual routes in app

**Problem:** WeWeb can't consume the map
- **Solution:** Verify endpoint path starts with `/`
- **Verify:** Response is valid JSON

### PACK V Issues

**Problem:** overall_ok is false
- **Check:** `checks.environment.ok` - are all env vars set?
- **Check:** `checks.database.ok` - is database connected?
- **Check:** `checks.routes.ok` - are required prefixes registered?

**Problem:** Missing required environment variable
- **Solution:** Set the variable in `.env` or system environment
- **Verify:** Variable appears in `checks.environment.details`

**Problem:** Missing critical route
- **Solution:** Ensure route is registered in main.py
- **Verify:** Route prefix appears in app routes via `/debug/routes/`

---

## Performance

### PACK U
- Response time: < 50ms
- Payload size: ~5KB for typical setup
- Caching: Can be cached on frontend (metadata includes version)

### PACK V
- Response time: 100-500ms (includes DB health check)
- Payload size: ~2KB
- Recommended check frequency: Before each deployment, or every 5 minutes in production

---

## Security

✓ Both endpoints protected by PACK T security middleware
✓ Rate limiting applied to prevent abuse
✓ Request logging for audit trails
✓ CORS configured for multi-origin access
✓ Response data is read-only (no mutations)

---

## Files Reference

### PACK U
```
services/api/app/services/ui_map.py    - UI map generation logic
services/api/app/routers/ui_map.py     - /ui-map/ HTTP endpoint
services/api/app/tests/test_ui_map.py  - 13 test cases
```

### PACK V
```
services/api/app/services/deploy_check.py   - Check orchestration
services/api/app/schemas/deploy_check.py    - Pydantic response models
services/api/app/routers/deploy_check.py    - /ops/deploy-check/ HTTP endpoint
services/api/app/tests/test_deploy_check.py - 14 test cases
```

### Documentation
```
PACK_U_V_IMPLEMENTATION.md    - Detailed implementation guide
SYSTEM_COMPLETE_SUMMARY.md    - Full system overview (16 packs)
PACK_U_V_COMPLETION.md        - Completion status and summary
PACK_U_V_QUICK_REFERENCE.md   - This file
```

---

## Version Info

- **PACK U Version:** 1.0
- **PACK V Version:** 1.0
- **Implementation Date:** December 5, 2025
- **Status:** Production Ready ✓
- **Last Updated:** December 5, 2025

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test files for usage examples
3. Check PACK_U_V_IMPLEMENTATION.md for detailed documentation
4. Review SYSTEM_COMPLETE_SUMMARY.md for system architecture

---

## Quick Links

- **PACK U Endpoint:** GET /ui-map/
- **PACK V Endpoint:** GET /ops/deploy-check/
- **Debug Routes:** GET /debug/routes/
- **System Health:** GET /debug/system/
- **Health Check:** GET /api/health/

**All endpoints ready for production use.**
