# VALHALLA BACKEND ACTIVATION GUIDE

**Date:** April 5, 2026  
**Version:** 1.0.0 - Launch Core  
**Status:** ✅ READY FOR WEWEB INTEGRATION

---

## 🚀 QUICK START

### Backend is Already Running!

Your Valhalla backend is currently running on **port 8000**.

**Verify it's working:**
```powershell
curl http://localhost:8000/health
# Returns: {"status":"ok","heimdall":"online"}
```

---

## 📡 CONNECTING WEWEB

### Step 1: Point WeWeb to Backend
Configure WeWeb API connector to:
- **API Base URL:** `http://localhost:8000` (development) or your production URL
- **CORS:** Already enabled for WeWeb domains
- **Documentation:** Available at `http://localhost:8000/docs`

### Step 2: Use Core API Endpoints

All 9 core routers are active:

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/api/leads` | Create, read, update leads | GET/POST/PUT |
| `/api/deals` | Manage deals from leads | GET/POST/PUT |
| `/api/offers` | Generate and manage offers | GET/POST |
| `/api/buyers` | Search and manage buyers | GET/POST |
| `/api/contracts` | Auto-generate contracts | POST/PUT |
| `/api/audit` | View audit trail | GET |
| `/api/health` | System health | GET |
| `/api/eia/monthly-report` | EIA compliance reports | GET |
| `/api/go-button/status` | Go-live decision status | GET |

### Step 3: Test Lead-to-Contract Flow

```bash
# 1. Create a lead
POST /api/leads
{
  "name": "John Doe",
  "property_address": "123 Main St",
  "estimated_value": 250000
}

# 2. Convert to deal
POST /api/deals/from-lead/{lead_id}
{
  "strategy": "wholesale"
}

# 3. Generate offer
POST /api/deals/offers/compute
{
  "deal_id": "{deal_id}",
  "margin": 0.20
}

# 4. Create contract
POST /api/contracts
{
  "deal_id": "{deal_id}",
  "offer_id": "{offer_id}"
}

# 5. Check audit trail
GET /api/audit/deals/{deal_id}
```

---

## 🎚️ FEATURE FLAGS

All experimental features are **DISABLED**:
```python
launch_core_only = True          # ✅ Core mode ACTIVE
enable_eia_tracking = True       # ✅ Compliance tracking ACTIVE
require_eia_compliance = True    # ✅ Strict compliance ACTIVE

# Disabled until phase 2:
enable_payments = False          # ❌ Payments disabled
enable_banking = False           # ❌ Banking disabled
enable_accounting = False        # ❌ Accounting disabled
enable_finops = False            # ❌ FinOps disabled
```

---

## 📊 EIA COMPLIANCE

The EIA (Expense Tracking & Income Analysis) system is fully integrated:

### EIA Endpoints
```bash
# Get EIA status
GET /api/eia/status

# Generate monthly report
GET /api/eia/monthly-report?month=2026-04

# Check compliance
GET /api/eia/check

# Build compliance packet
POST /api/eia/build-packet
{
  "deal_id": "{deal_id}",
  "month": "2026-04"
}
```

### EIA Report Includes
- Income summary
- Expense summary
- Receipt index
- Bank checklist
- Declaration notes

---

## 🔍 MONITORING & DIAGNOSTICS

### Health Endpoints
```bash
# Primary health check
GET /health
# Response: {"status":"ok","heimdall":"online"}

# Secondary health check
GET /healthz
# Response: {"status":"ok"}

# System version info
GET /version
# Response: {"service":"valhalla-api","version":"1.0.0"}

# All active routes
GET /__routes
```

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **ReDoc:** http://localhost:8000/redoc (if enabled)

### System Test
```bash
# Run backend test suite
python services/api/tests_backend.py
```

---

## 🛠️ SERVER MANAGEMENT

### View Server Logs
```powershell
# Terminal is already running - watch for output
# Check for errors or warnings
```

### Restart Server
```powershell
# Kill current server (Ctrl+C in running terminal)
# Then restart:

$env:DATABASE_URL="sqlite:///./valhalla_local.db"
$env:VALHALLA_JWT_SECRET="dev-secret-key-change-in-production"
$env:SKIP_MIGRATIONS="1"
python -m uvicorn app.main:app --reload --port 8000
```

### Change Port
```powershell
# Modify the launch command:
python -m uvicorn app.main:app --reload --port 9000
# Then use http://localhost:9000
```

---

## 🔐 SECURITY NOTES

### For Development
- ✅ CORS enabled for localhost and WeWeb domains
- ✅ Debug mode enabled
- ✅ Documentation public
- ✅ Auto-reload enabled

### For Production
- 🔒 Disable debug mode: `DEBUG=false`
- 🔒 Use environment-specific secrets
- 🔒 Restrict CORS origins
- 🔒 Use HTTPS only
- 🔒 Disable /docs endpoint
- 🔒 Use strong JWT secret

---

## 🆘 TROUBLESHOOTING

### Server Won't Start
**Problem:** `ValidationError: DATABASE_URL required`  
**Solution:** Set environment variable:
```powershell
$env:DATABASE_URL="sqlite:///./valhalla_local.db"
$env:VALHALLA_JWT_SECRET="your-secret-key"
```

### Routes Timing Out
**Problem:** API calls take too long  
**Solution:** 
1. Check database performance
2. Review server logs for errors
3. Increase request timeout in WeWeb

### EIA Endpoint Returns 404
**Problem:** EIA endpoints not found  
**Solution:** Verify router is registered in `app/main.py`

### CORS Errors
**Problem:** WeWeb can't connect  
**Solution:** 
1. Verify CORS_ALLOWED_ORIGINS includes WeWeb domain
2. Check browser console for exact error
3. Ensure backend is running on correct port

---

## 📋 DEPLOYMENT CHECKLIST

Before going live:

- [ ] Backend running without errors
- [ ] All health checks passing
- [ ] WeWeb successfully connects
- [ ] Lead-to-contract flow tested
- [ ] EIA reports generating
- [ ] Audit trail recording events
- [ ] Error logging configured
- [ ] Performance tested
- [ ] Security review completed
- [ ] Backup system verified

---

## 🎯 NEXT PHASES

### Phase 2: Advanced Features (When Ready)
- [ ] Enable payments integration
- [ ] Enable banking integration
- [ ] Enable accounting integration
- [ ] Enable FinOps system
- [ ] Enable Heimdall autonomy

### Phase 3: Production Deployment
- [ ] Docker containerization
- [ ] Production database setup
- [ ] SSL certificate configuration
- [ ] Load balancer setup
- [ ] Monitoring and alerting

---

## 📞 SUPPORT

For issues or questions, check:
1. Server logs (current terminal)
2. API documentation: `/docs`
3. System self-test: `/api/system/selftest`
4. Memory notes: `/memories/repo/`

---

## 🎬 SUMMARY

Your Valhalla backend is now:
- ✅ **Operational** on port 8000
- ✅ **EIA-compliant** with reporting
- ✅ **Feature-flagged** for launch-only mode
- ✅ **API-documented** and discoverable
- ✅ **Ready for WeWeb integration**

**Start building with WeWeb now!**

---

*Last Updated: April 5, 2026 - Backend v1.0.0 Launch Core*
