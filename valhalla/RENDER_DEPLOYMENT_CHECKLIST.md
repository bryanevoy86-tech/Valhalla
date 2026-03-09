# Render Deployment: Production Contract Pipeline (S3 + Webhooks)

## Quick Summary

Your production Contract Pipeline is **ready to deploy**. All code is committed and pushed to GitHub.

### What Changed

**Commit `ac54f8e`:** Production Contract Pipeline
- S3 storage backend (AWS S3, Cloudflare R2, Wasabi, B2)
- DocuSign-ready webhook receiver
- Template seeding system
- Presigned URL downloads (production-safe)
- Full audit logging

**Commit `676f422`:** Documentation + Test Script

**Commit `bb2c968`:** Alembic migration fix (multiple heads resolved)

---

## Deploy to Render (3 Steps)

### 1. Add Render Environment Variables

Go to **Render Dashboard → Valhalla API → Environment**

Add these variables:

```
# Contract Pipeline Storage (S3)
CONTRACT_STORAGE_BACKEND=s3
CONTRACT_S3_BUCKET=valhalla-contracts
CONTRACT_S3_PREFIX=prod/contracts

# AWS Credentials (choose one below)

# Option A: AWS S3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>

# Option B: Cloudflare R2
AWS_REGION=auto
AWS_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_ACCESS_KEY_ID=<your-r2-access-key>
AWS_SECRET_ACCESS_KEY=<your-r2-secret-key>

# Option C: Wasabi
AWS_REGION=us-east-1
AWS_ENDPOINT_URL=https://s3.wasabisys.com
AWS_ACCESS_KEY_ID=<your-wasabi-access-key>
AWS_SECRET_ACCESS_KEY=<your-wasabi-secret-key>

# Optional Security (recommended for production)
CONTRACT_S3_SSE=AES256
```

### 2. Trigger Render Build

In Render dashboard:
1. Go to **Valhalla API → Manual Deploy**
2. Click **Deploy latest commit**
3. Watch logs for:
   - Docker build: ✅ SUCCESS
   - Migrations: `alembic upgrade head` ✅ SUCCESS
   - Startup: `Application startup complete` ✅ SUCCESS

### 3. Verify Deployment

```bash
# Test health endpoint
curl https://your-app.onrender.com/health

# Seed templates
curl -X POST https://your-app.onrender.com/api/contracts/templates/seed

# Expected response
{
  "ok": true,
  "created": 2
}
```

---

## What Works Out of the Box

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/contracts` | POST | Create contract from template | ✅ Ready |
| `/api/contracts/{id}/state` | POST | Transition state | ✅ Ready |
| `/api/contracts/{id}/upload` | POST | Upload PDF to S3 | ✅ Ready |
| `/api/contracts/{id}/send` | POST | Send for signature (Sandbox) | ✅ Ready |
| `/api/contracts/{id}/documents/{id}/download` | GET | Presigned S3 URL | ✅ Ready |
| `/api/contracts/{id}/events` | GET | Audit trail | ✅ Ready |
| `/api/contracts/templates/seed` | POST | Initialize templates | ✅ Ready |
| `/api/contracts/webhooks/provider` | POST | Webhook receiver | ✅ Ready |

---

## Production Features

### Storage
- **S3-compatible**: Works with AWS S3, Cloudflare R2, Wasabi, Backblaze B2
- **Immutable blobs**: All documents addressed by SHA256 hash
- **Presigned URLs**: 15-minute download links (no inline file serving)
- **Encryption**: Optional AES256 or AWS KMS

### State Machine
```
DRAFT
  ↓
READY_FOR_REVIEW → IN_REVIEW
  ↓
APPROVED_FOR_SIGNATURE
  ↓
SENT_FOR_SIGNATURE → PARTIALLY_SIGNED → FULLY_EXECUTED
  ↓
DECLINED → ARCHIVED
  ↓
VOIDED → ARCHIVED
```

### Audit Trail
Every action logged to `contract_events` table:
- CONTRACT_CREATED
- DOCUMENT_UPLOADED
- STATE_CHANGED
- SIGNATURE_SENT
- PROVIDER_WEBHOOK (from DocuSign)
- etc.

### Templates
Two default templates seeded:
1. **WHOLESALE_PURCHASE_AGREEMENT** - Property acquisition
2. **ASSIGNMENT_AGREEMENT** - Assignment to end buyer

Easily extensible: add more in `seed_templates.py`

---

## DocuSign Integration (Next Phase)

When ready:
1. Create `app/services/contracts/provider_docusign.py`
2. Implement `SignatureProvider` ABC
3. Update `service.py` to load DocuSign provider
4. Configure DocuSign API credentials in Render environment
5. Deploy

Webhook endpoint is **already ready**: `POST /api/contracts/webhooks/provider`

---

## Files Added/Modified

### New Files
- `app/services/contracts/storage_s3.py` - S3 storage implementation
- `app/services/contracts/seed_templates.py` - Template seeding
- `app/routers/contracts_webhooks.py` - Webhook receiver
- `alembic/versions/20260205_contract_pipeline_s3.py` - Database migration
- `CONTRACT_PIPELINE_S3_DEPLOYMENT.md` - Full deployment guide
- `test_contract_pipeline.ps1` - Automated test script

### Modified Files
- `app/services/contracts/service.py` - S3 backend support
- `app/routers/contracts_pipeline.py` - Download + seed endpoints
- `app/main.py` - Register webhooks router
- `services/api/requirements.txt` - boto3 already present

### Migrations
- `20260205_merge_floor_and_contracts` - Merges Alembic heads
- `20260205_contract_pipeline_s3` - Creates contract tables

---

## Deployment Validation

Check Render logs for these messages:

```
✅ Context impl PostgresqlImpl.
✅ Running upgrade 20260205_merge_floor_and_contracts
✅ Running upgrade 20260205_contract_pipeline_s3
✅ [main.py] Contracts_pipeline router registered
✅ [main.py] Contracts_webhooks router registered
✅ Application startup complete
```

---

## Testing Flow (Local Dev)

```powershell
# Start server
$env:PYTHONPATH="C:\dev\valhalla\services\api"
$env:DATABASE_URL="sqlite:///dev.db"
$env:VALHALLA_JWT_SECRET="dev-secret"
$env:VALHALLA_API_KEY="dev-key"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# In another terminal
cd C:\dev\valhalla
.\test_contract_pipeline.ps1 -BaseUrl http://localhost:8000
```

All 8 tests should PASS.

---

## Next Steps After Deploy

1. **Verify S3 bucket is accessible**
   ```bash
   aws s3 ls s3://valhalla-contracts/ --region us-east-1
   ```

2. **Test presigned URL downloads**
   - Upload document
   - Get download URL
   - Open in browser (should work for 15 minutes)

3. **Monitor logs** for webhook activity (once DocuSign is integrated)

4. **Review audit trail** - all state changes are tracked

5. **Plan DocuSign integration** for next phase

---

## Commit History (Latest)

```
676f422 - docs: Production Contract Pipeline S3 deployment guide + test script
ac54f8e - feat: Production-grade Contract Pipeline with S3 storage, webhooks, and templates
bb2c968 - Fix: Create merge migration to unify floor control and contract pipeline heads
```

---

## Support

- **Schema questions?** See [CONTRACT_PIPELINE_S3_DEPLOYMENT.md](CONTRACT_PIPELINE_S3_DEPLOYMENT.md)
- **Endpoint examples?** See `test_contract_pipeline.ps1`
- **S3 configuration?** Check AWS IAM permissions for bucket access
- **Migration issues?** Run `python -m alembic history` to verify chain

---

**Status: ✅ READY FOR RENDER DEPLOYMENT**

Just add environment variables and trigger deploy!
