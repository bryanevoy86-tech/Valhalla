# Testing Guide

## Local Testing Setup

### 1. Install Dependencies

```bash
cd services/api
pip install -r requirements.txt
```

### 2. Run Smoke Tests

**Against local API (Docker):**
```bash
# Start Docker first
docker-compose up -d

# Run tests
cd services/api
API_BASE=http://localhost:4000 pytest -q tests/test_smoke.py
```

**Against Render:**
```bash
cd services/api
API_BASE=https://valhalla-api-ha6a.onrender.com/api BUILDER_KEY=your-key pytest -q tests/test_smoke.py
```

### 3. Run Tests with Coverage

```bash
cd services/api
pytest -q --cov --cov-config=../../.coveragerc --cov-report=term-missing
```

**Coverage requirements:**
- Minimum: 95%
- Shows missing lines
- Skips fully covered files

### 4. Run Type Checking

```bash
# From project root
mypy services/api/app --config-file=mypy.ini
```

### 5. Run Performance Smoke Tests

**Local:**
```bash
API_BASE=http://localhost:4000 python tools/perf_smoke.py
```

**Render:**
```bash
API_BASE=https://valhalla-api-ha6a.onrender.com P50_MAX_MS=400 python tools/perf_smoke.py
```

**Performance thresholds:**
- Local: 300ms p50
- Render: 400ms p50 (accounts for network latency)

---

## CI/CD Pipeline

**Triggers:**
- Every push to `main`
- Every pull request to `main`

**Steps:**
1. ✅ **Unit & Smoke Tests** - pytest with ≥95% coverage
2. ✅ **Type Checking** - mypy strict mode
3. ✅ **Performance Smoke** - p50 latency check against Render

**Required GitHub Secrets:**
- `VALHALLA_API_BASE` - https://valhalla-api-ha6a.onrender.com
- `VALHALLA_BUILDER_KEY` - Your builder API key

---

## Test Structure

```
services/api/tests/
├── __init__.py
└── test_smoke.py         # FastAPI endpoint smoke tests
```

**test_smoke.py:**
- `test_healthz()` - Health check endpoint
- `test_builder_list_tasks()` - Builder tasks with auth
- `test_research_playbooks_list_public()` - Public playbooks

---

## Config Files

- **`.coveragerc`** - Coverage configuration (95% minimum)
- **`mypy.ini`** - Type checking rules (strict mode)
- **`.github/workflows/ci.yml`** - CI/CD pipeline

---

## Quick Commands

```bash
# Run everything locally
cd services/api
pytest -q --cov --cov-config=../../.coveragerc --cov-report=term-missing
cd ../..
mypy services/api/app
API_BASE=http://localhost:4000 python tools/perf_smoke.py

# Just smoke tests
cd services/api
API_BASE=http://localhost:4000 pytest -q tests/test_smoke.py

# Just performance
API_BASE=http://localhost:4000 python tools/perf_smoke.py
```

---

## Troubleshooting

**Coverage below 95%:**
- Add unit tests for uncovered code
- Or adjust `.coveragerc` fail_under threshold

**Mypy errors:**
- Add type hints to functions
- Use `# type: ignore` for unavoidable errors
- Check `mypy.ini` for configuration

**Performance failures:**
- Check if API is running
- Increase `P50_MAX_MS` for slower environments
- Look for slow database queries or external API calls

**Smoke test failures:**
- Verify API_BASE is correct
- Check BUILDER_KEY is set
- Ensure endpoints are deployed (research endpoints may need migration)

---

## Next Steps

1. Add more unit tests to reach 95% coverage
2. Add integration tests for research/embeddings
3. Add load tests for capacity planning
4. Add security tests (bandit, safety)
