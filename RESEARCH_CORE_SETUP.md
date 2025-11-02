# 🧠 Heimdall Research Core - Complete Setup Guide

## ✅ What's Deployed

Heimdall's Research Core is now live with:
- **Research Sources** - manage documentation URLs
- **Auto-Ingestion** - fetch and parse web content
- **Query Engine** - keyword search across ingested docs
- **Playbooks** - structured lessons for Heimdall
- **Jobs Endpoint** - secured background job triggers
- **Nightly Automation** - GitHub Actions workflow

---

## 🔐 GitHub Secrets Setup

To enable nightly auto-ingestion, add these secrets to your GitHub repository:

1. Go to: **GitHub.com** → **bryanevoy86-tech/Valhalla** → **Settings** → **Secrets and variables** → **Actions**

2. Click **"New repository secret"** and add:

### Secret 1: VALHALLA_API_BASE
```
https://valhalla-api-ha6a.onrender.com
```

### Secret 2: VALHALLA_BUILDER_KEY
```
<your HEIMDALL_BUILDER_API_KEY from Render env vars>
```

---

## 📡 API Endpoints Reference

### Research Sources
```bash
# List all sources
GET /api/research/sources
Header: X-API-Key: <your_key>

# Add a new source
POST /api/research/sources
Header: X-API-Key: <your_key>
Body: {
  "name": "FastAPI Docs",
  "url": "https://fastapi.tiangolo.com/",
  "kind": "web",
  "ttl_seconds": 86400,
  "enabled": true
}

# Ingest a specific source
POST /api/research/ingest
Header: X-API-Key: <your_key>
Body: {
  "source_id": 1
}

# Query ingested content
POST /api/research/query
Header: X-API-Key: <your_key>
Body: {
  "q": "Response Model",
  "limit": 5
}
```

### Playbooks
```bash
# List all playbooks (no auth required)
GET /api/playbooks

# Get specific playbook
GET /api/playbooks/{slug}

# Create playbook
POST /api/playbooks
Header: X-API-Key: <your_key>
Body: {
  "slug": "builder-safety-rules",
  "title": "Builder Safety Rules",
  "body_md": "1. Rule one\n2. Rule two",
  "enabled": true
}
```

### Jobs (New!)
```bash
# Trigger nightly ingest manually (async)
POST /api/jobs/research/ingest_all
Header: X-API-Key: <your_key>
Response: {"ok": true, "job": "research.ingest_all", "status": "started"}

# Synchronous version (for testing)
POST /api/jobs/research/ingest_all_sync
Header: X-API-Key: <your_key>
Response: {
  "ok": true,
  "job": "research.ingest_all",
  "total_sources": 2,
  "success": 2,
  "errors": 0,
  "results": [...]
}
```

---

## 🧪 Testing Locally

### Quick Test (PowerShell)
```powershell
# Run the provided test script
.\test-research-core.ps1
```

### Manual Test
```powershell
$api = "http://localhost:8000/api"  # or your Render URL
$key = "test123"  # your API key

# Test jobs endpoint
curl.exe -X POST "$api/jobs/research/ingest_all" -H "X-API-Key: $key"

# Expected: {"ok":true,"job":"research.ingest_all","status":"started"}
```

---

## 🌐 Testing on Render

```powershell
$api = "https://valhalla-api-ha6a.onrender.com/api"
$key = "<your_render_key>"

# Manually trigger ingest
curl.exe -X POST "$api/jobs/research/ingest_all" -H "X-API-Key: $key"
```

---

## ⏰ Nightly Automation

The GitHub Actions workflow `.github/workflows/nightly-ingest.yml` runs:
- **Time**: Every night at 02:15 America/Winnipeg (08:15 UTC)
- **Action**: Calls `/api/jobs/research/ingest_all` on your Render API
- **Auth**: Uses `VALHALLA_BUILDER_KEY` secret

### Manual Trigger
1. Go to **Actions** tab in GitHub
2. Select **"Nightly Research Ingest"**
3. Click **"Run workflow"** → **"Run workflow"**

---

## 🎨 WeWeb Integration (Optional)

Add a button to your Builder Console to trigger ingest on-demand:

### Workflow: `runIngestNow`
- **Method**: POST
- **URL**: `{{ api_base_url }}/jobs/research/ingest_all`
- **Headers**: `X-API-Key: {{ builderApiKey }}`
- **On Success**: Toast "Ingest started!"

### Button Config
- **Label**: "🧠 Run Ingest Now"
- **Action**: Trigger `runIngestNow` workflow
- **Keep AI context OFF** (manual REST request)

---

## 📊 Monitoring & Safety

### Check Ingestion Status
```powershell
# View all sources and last ingestion time
curl.exe "$api/research/sources" -H "X-API-Key: $key"
```

### Rate Limiting (Optional Enhancement)
Consider adding a `job_runs` table to track:
- Last run timestamp
- Skip if run within last 1 hour
- Log success/failure counts

```sql
CREATE TABLE job_runs (
  id SERIAL PRIMARY KEY,
  job_name VARCHAR(100),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status VARCHAR(20),
  result_json TEXT
);
```

---

## 🚀 Next Steps

1. ✅ **Verify GitHub Secrets** are set
2. ✅ **Test manually** via `/api/jobs/research/ingest_all`
3. ✅ **Trigger workflow** manually to verify it works
4. 🔄 **Wait for first nightly run** at 02:15 AM
5. 📈 **Add more sources** as Heimdall learns

---

## 📝 Files Created

- `services/api/app/models/research.py` - ResearchSource, ResearchDoc, ResearchQuery, Playbook models
- `services/api/app/schemas/research.py` - Pydantic schemas
- `services/api/app/routers/research.py` - Research endpoints
- `services/api/app/routers/playbooks.py` - Playbooks endpoints
- `services/api/app/routers/jobs.py` - Jobs endpoints (NEW)
- `services/api/app/jobs/research_jobs.py` - Background job logic (NEW)
- `services/api/alembic/versions/v3_3_research.py` - Database migration
- `.github/workflows/nightly-ingest.yml` - Nightly automation (NEW)
- `test-research-core.ps1` - Local test script

---

## 🎯 Success Criteria

✅ `/docs` shows `/api/research/*`, `/api/playbooks`, `/api/jobs/*` endpoints  
✅ Can add sources via POST `/api/research/sources`  
✅ Can ingest sources via POST `/api/research/ingest`  
✅ Can query content via POST `/api/research/query`  
✅ Jobs endpoint returns `{"ok":true}`  
✅ GitHub Actions workflow runs successfully  
✅ Nightly ingestion happens at 02:15 AM Winnipeg time  

---

## 🔮 Future Enhancements

1. **Vector Embeddings** - semantic search with OpenAI/Cohere
2. **Builder Integration** - use research docs when generating code
3. **Slack Notifications** - alert on ingest failures
4. **Dashboard** - visualize sources, query patterns, doc growth
5. **Multi-language Support** - ingest from non-English sources

---

**Heimdall is now continuously learning! 🧠✨**
