# Contract Pipeline Quick Reference Card

## Environment Setup (Render)

```
CONTRACT_STORAGE_BACKEND=s3
CONTRACT_S3_BUCKET=valhalla-contracts
CONTRACT_S3_PREFIX=prod/contracts
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
```

## API Endpoints

### Create Contract
```bash
POST /api/contracts
{
  "template_code": "ASSIGNMENT_AGREEMENT",
  "title": "Assignment - 123 Main St",
  "deal_id": "DEAL123",
  "merge_data": {...},
  "parties": [{role, name, email, must_sign}, ...],
  "sign_provider": "SANDBOX"
}
→ {id, state: DRAFT, ...}
```

### Upload Document
```bash
POST /api/contracts/{id}/upload
  multipart: file (PDF)
→ {ok: true, doc_id, filename}
```

### Change State
```bash
POST /api/contracts/{id}/state
{
  "target": "APPROVED_FOR_SIGNATURE|SENT_FOR_SIGNATURE|...",
  "note": "..."
}
→ {id, state, ...}
```

### Send for Signature
```bash
POST /api/contracts/{id}/send
{
  "subject": "Please sign",
  "message": "..."
}
→ {ok: true, envelope_id, provider_envelope_id, status}
```

### Download Document (S3 Presigned URL)
```bash
GET /api/contracts/{id}/documents/{doc_id}/download
→ {ok: true, url: "https://...", filename, expires_seconds: 900}
```

### Audit Trail
```bash
GET /api/contracts/{id}/events
→ [{id, event_type, actor, meta, created_at}, ...]
```

### Seed Templates
```bash
POST /api/contracts/templates/seed
→ {ok: true, created: 2}
```

### Webhook (DocuSign/Sandbox)
```bash
POST /api/contracts/webhooks/provider
{
  "provider_envelope_id": "...",
  "status": "completed|declined|delivered|partially_signed",
  ...
}
→ {ok: true}
```

## State Machine

```
DRAFT → READY_FOR_REVIEW → IN_REVIEW → APPROVED_FOR_SIGNATURE
        ↓                    ↓          ↓
        └────────────────────┼──────────→ SENT_FOR_SIGNATURE
                             ↓                    ↓
                          VOIDED                 ├─→ PARTIALLY_SIGNED ──┐
                             ↓                   ├─→ DECLINED          │
                          ARCHIVED           ←───┴─→ FULLY_EXECUTED ←──┘
                                                    ↓
                                                 ARCHIVED
```

## S3 Providers Supported

| Provider | Endpoint | Region |
|----------|----------|--------|
| AWS S3 | https://s3.amazonaws.com | us-east-1 |
| Cloudflare R2 | https://{id}.r2.cloudflarestorage.com | auto |
| Wasabi | https://s3.wasabisys.com | us-east-1 |
| Backblaze B2 | https://s3.{region}.backblazeb2.com | us-west-002 |

## Local Testing

```bash
# Start server
export DATABASE_URL="sqlite:///dev.db"
export VALHALLA_JWT_SECRET="dev-secret"
python -m uvicorn app.main:app --port 8000

# Run tests
./test_contract_pipeline.ps1 -BaseUrl http://localhost:8000

# Validate config
python services/api/validate_s3_config.py
```

## Common Issues

| Issue | Solution |
|-------|----------|
| S3 access denied | Check AWS IAM permissions + bucket name |
| Migration fails | Run `alembic upgrade head` (chain now linear) |
| Presigned URL 404 | Check S3 bucket exists + document was uploaded |
| Templates not seeding | Run `/api/contracts/templates/seed` endpoint |
| Webhook failing | Check provider_envelope_id matches DB record |

## Files Reference

| File | Purpose |
|------|---------|
| `app/services/contracts/storage_s3.py` | S3 storage implementation |
| `app/services/contracts/service.py` | Contract state machine |
| `app/routers/contracts_pipeline.py` | CRUD endpoints |
| `app/routers/contracts_webhooks.py` | Webhook receiver |
| `alembic/versions/20260205_contract_pipeline_s3.py` | DB schema |
| `test_contract_pipeline.ps1` | 8-test validation suite |
| `services/api/validate_s3_config.py` | Pre-deployment checker |

## Next Phase: DocuSign

1. Create `app/services/contracts/provider_docusign.py`
2. Implement `SignatureProvider` ABC
3. Configure `SIGN_PROVIDER=docusign` + API credentials
4. Update webhook to verify DocuSign signatures
5. Deploy

## Deployment Checklist

- [ ] Add Render environment variables
- [ ] Trigger deploy: `Manual Deploy → Deploy latest commit`
- [ ] Watch logs for ✅ Docker build, ✅ Migrations, ✅ Startup
- [ ] Test: `POST /api/contracts/templates/seed`
- [ ] Verify S3 bucket: `aws s3 ls s3://valhalla-contracts/`
- [ ] Run full test suite: `./test_contract_pipeline.ps1`

## Command Reference

```bash
# Check Alembic migration chain
alembic heads                    # Should show 1 head now (fixed!)
alembic history                  # Linear chain

# List contracts in DB
psql -c "SELECT id, state, created_at FROM contracts ORDER BY created_at DESC LIMIT 5;"

# List documents in S3
aws s3 ls s3://valhalla-contracts/prod/contracts/ --recursive

# View contract events (audit trail)
psql -c "SELECT event_type, actor, created_at FROM contract_events WHERE contract_id='...';"
```

## Current Status

✅ All code committed and pushed to GitHub
✅ All migrations applied (linear chain)
✅ All endpoints implemented and tested
✅ S3 storage ready for any provider
✅ Documentation complete
✅ Ready for Render production deployment

**Last Commit**: `8911bf1` - Production pipeline complete

