# Production Contract Pipeline (S3 + Render Deployment Guide)

## Overview

This production-grade contract pipeline includes:
- **S3-compatible storage** (AWS S3, Cloudflare R2, Wasabi, Backblaze B2)
- **State machine** (DRAFT → APPROVED_FOR_SIGNATURE → SENT_FOR_SIGNATURE → FULLY_EXECUTED)
- **Full audit trail** (all state changes + events logged)
- **Webhook ingress** (DocuSign-ready signature status updates)
- **Template system** (merge schema for document generation)
- **Presigned URLs** (production-safe file downloads, no inline serving)

## Architecture

```
POST /api/contracts                      # Create contract from template
POST /api/contracts/{id}/upload          # Upload draft PDF to S3
POST /api/contracts/{id}/state           # State machine transitions
POST /api/contracts/{id}/send            # Send to signature provider
GET  /api/contracts/{id}/events          # Audit trail
GET  /api/contracts/{id}/documents/{id}/download  # Presigned URL
POST /api/contracts/templates/seed       # Initialize templates
POST /api/contracts/webhooks/provider    # Webhook from DocuSign/sandbox
```

## Deployment Configuration

### Render Environment Variables

**Required:**
```
CONTRACT_STORAGE_BACKEND=s3                    # Storage backend (s3 or local)
CONTRACT_S3_BUCKET=valhalla-contracts          # S3 bucket name
CONTRACT_S3_PREFIX=prod/contracts              # S3 key prefix (optional but recommended)
AWS_REGION=us-east-1                           # AWS region
AWS_ACCESS_KEY_ID=<your-key>                   # AWS credentials
AWS_SECRET_ACCESS_KEY=<your-secret>
```

**For AWS S3:**
```
# Use standard AWS credentials above
# Endpoint URL is inferred: https://s3.amazonaws.com
```

**For Cloudflare R2:**
```
AWS_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_REGION=auto
# Use R2 API tokens as AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

**For Wasabi:**
```
AWS_ENDPOINT_URL=https://s3.wasabisys.com
AWS_REGION=us-east-1
# Use Wasabi API credentials
```

**Optional (Security & Encryption):**
```
CONTRACT_S3_SSE=AES256                         # Server-side encryption (AES256 or aws:kms)
CONTRACT_S3_KMS_KEY_ID=<kms-key-arn>          # AWS KMS key (if using aws:kms)
```

## Go-Live Checklist

### 1. Pre-Deployment (Local Dev)

```bash
# Install dependencies
python -m pip install boto3

# Test local migrations
export DATABASE_URL="sqlite:///dev.db"
export VALHALLA_JWT_SECRET="dev-secret"
python -m alembic upgrade head

# Start server
export PYTHONPATH="/path/to/services/api"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Render Deployment

1. **Commit code to main**
   ```bash
   git push origin main
   ```

2. **Render automatically builds and deploys**
   - Docker build (python:3.11-slim)
   - Migrations run: `alembic upgrade head`
   - Server starts: `uvicorn app.main:app --host 0.0.0.0 --port 10000`

3. **Check deployment logs** at render.com dashboard

### 3. Post-Deployment Tests

**A. Seed Templates**
```bash
curl -X POST https://your-app.onrender.com/api/contracts/templates/seed
```

Expected response:
```json
{
  "ok": true,
  "created": 2
}
```

**B. Create Contract**
```bash
curl -X POST https://your-app.onrender.com/api/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "template_code": "ASSIGNMENT_AGREEMENT",
    "title": "Assignment - 123 Main St",
    "deal_id": "DEAL123",
    "merge_data": {
      "assignor_name": "Your Co",
      "assignee_name": "Buyer LLC",
      "assignment_fee": 15000
    },
    "parties": [
      {
        "role": "ASSIGNOR",
        "name": "Your Co",
        "email": "you@example.com",
        "must_sign": true
      },
      {
        "role": "ASSIGNEE",
        "name": "Buyer LLC",
        "email": "buyer@example.com",
        "must_sign": true
      }
    ],
    "sign_provider": "SANDBOX"
  }'
```

Expected response:
```json
{
  "id": "abc123...",
  "state": "DRAFT",
  "title": "Assignment - 123 Main St",
  ...
}
```

Save the `id` for next steps.

**C. Upload Draft PDF**
```bash
curl -X POST https://your-app.onrender.com/api/contracts/{id}/upload \
  -F "file=@contract.pdf" \
  -F "kind=DRAFT"
```

Expected response:
```json
{
  "ok": true,
  "doc_id": "doc-xyz...",
  "filename": "contract.pdf",
  "kind": "DRAFT"
}
```

**D. Transition to APPROVED_FOR_SIGNATURE**
```bash
curl -X POST https://your-app.onrender.com/api/contracts/{id}/state \
  -H "Content-Type: application/json" \
  -d '{
    "target": "APPROVED_FOR_SIGNATURE",
    "note": "Ready to send for signature"
  }'
```

Expected response:
```json
{
  "id": "abc123...",
  "state": "APPROVED_FOR_SIGNATURE",
  ...
}
```

**E. Send for Signature**
```bash
curl -X POST https://your-app.onrender.com/api/contracts/{id}/send \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Please sign the contract",
    "message": "Review and sign at your earliest convenience"
  }'
```

Expected response:
```json
{
  "ok": true,
  "envelope_id": "env-abc...",
  "provider_envelope_id": "sandbox-1234...",
  "status": "created"
}
```

**F. Download Document (Presigned URL)**
```bash
curl -X GET https://your-app.onrender.com/api/contracts/{id}/documents/{doc_id}/download
```

Expected response:
```json
{
  "ok": true,
  "url": "https://valhalla-contracts.s3.amazonaws.com/prod/contracts/abc123/sha256_contract.pdf?...",
  "filename": "contract.pdf",
  "content_type": "application/pdf",
  "expires_seconds": 900
}
```

The `url` is valid for 15 minutes and can be shared with clients.

**G. Check Audit Trail**
```bash
curl -X GET https://your-app.onrender.com/api/contracts/{id}/events
```

Expected response:
```json
[
  {
    "id": "evt-1",
    "event_type": "CONTRACT_CREATED",
    "actor": "system",
    "created_at": "2026-02-05T...",
    ...
  },
  {
    "id": "evt-2",
    "event_type": "DOCUMENT_UPLOADED",
    "actor": "system",
    ...
  },
  ...
]
```

## DocuSign Integration (Future)

When ready to integrate DocuSign:

1. **Create DocuSign adapter**: `app/services/contracts/provider_docusign.py`
   - Implement `SignatureProvider` ABC
   - Override `create_envelope()` and `get_status()`
   - Parse DocuSign API responses

2. **Update service.py**: Add `elif backend == "docusign"` to `_resolve_provider()`

3. **Update webhook receiver**: Parse real DocuSign payloads
   - Verify signature with DocuSign webhook secret
   - Map DocuSign status to contract state

4. **Test in Render**:
   - Set `SIGN_PROVIDER=docusign` in environment
   - Configure DocuSign API credentials
   - Webhook endpoint: `POST /api/contracts/webhooks/provider`

## Database Schema

### Migrations

- **20260205_merge_floor_and_contracts**: Merges floor control plane + contract pipeline heads
- **20260205_contract_pipeline_s3**: Creates all contract tables (Postgres-first)

### Tables

| Table | Purpose |
|-------|---------|
| `contract_templates` | Document templates with merge schema |
| `contracts` | Main contract entity with state machine |
| `contract_parties` | Signers (roles, emails, provider IDs) |
| `contract_documents` | Uploaded PDFs (S3-addressed, immutable) |
| `contract_envelopes` | Signature provider integration (envelopes, statuses) |
| `contract_events` | Full audit trail (state changes, uploads, webhooks) |

## Storage Layer

### Local (Development)

```python
from app.services.contracts.storage import LocalContractStorage
storage = LocalContractStorage("./.contract_store")
```

### S3 (Production - Default)

```python
from app.services.contracts.storage_s3 import S3ContractStorage
storage = S3ContractStorage()
# Reads: CONTRACT_S3_BUCKET, CONTRACT_S3_PREFIX, AWS_* env vars
```

Both implement the same interface:
- `put_bytes(contract_id, filename, data) -> StoredObject`
- `get_bytes(storage_key) -> bytes`
- `exists(storage_key) -> bool`
- `presign_get(storage_key, expires_seconds=900) -> str` (S3 only)

## Environment Validation

Before deploying to Render:

```bash
# Check S3 bucket is accessible
aws s3 ls s3://valhalla-contracts/ --region us-east-1

# Test Alembic migration
export DATABASE_URL="postgresql://..."  # Your Render DB
export VALHALLA_JWT_SECRET="dev-secret"
python -m alembic upgrade head

# Seed templates
curl -X POST http://localhost:8000/api/contracts/templates/seed
```

## Troubleshooting

### Migration fails: "Multiple head revisions"

This is **now fixed** by merge migration `20260205_merge_floor_and_contracts`. If you see this:

1. Ensure you've pulled latest code: `git pull origin main`
2. Re-run migration: `python -m alembic upgrade head`

### S3 access denied

Check:
- S3 bucket exists
- IAM credentials have `s3:GetObject`, `s3:PutObject`, `s3:HeadObject` permissions
- Environment variables are set correctly
- Bucket region matches `AWS_REGION`

### Presigned URL expires too quickly

Default is 900 seconds (15 minutes). To change:
- Edit `download_doc()` in `app/routers/contracts_pipeline.py`
- Change `expires_seconds` parameter (max 604800 = 7 days for AWS S3)

### Documents not persisting between requests

This is expected behavior if using local storage (`CONTRACT_STORAGE_BACKEND=local`). Use S3 for production.

## Production Recommendations

1. **Always use S3** (or compatible) in production
2. **Enable encryption**: Set `CONTRACT_S3_SSE=AES256` or use KMS
3. **Monitor costs**: S3 charges for GET/PUT/LIST operations
4. **Backup strategy**: S3 versioning or cross-region replication
5. **Document retention**: Set S3 lifecycle policies if needed
6. **Webhook security**: Verify DocuSign signatures in production
7. **Audit logging**: All state changes are in `contract_events` table

## Commit History

- `bb2c968`: Fix Alembic multiple heads (merge migration)
- `ac54f8e`: Production Contract Pipeline (S3 + webhooks + templates)

Ready to deploy to Render!
