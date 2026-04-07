# VALHALLA ACTIVATION SYSTEM - INTEGRATION & DEPLOYMENT GUIDE
==============================================================

## Integration with Main Application

### 1. Register Activation Routes

Add to your main FastAPI app (`app/main.py`):

```python
from fastapi import FastAPI
from app.routes.activation import router as activation_router

app = FastAPI(title="VALHALLA API")

# Register activation routes
app.include_router(activation_router)

# All activation endpoints now available at /api/v1/activation/*
```

### 2. Initialize Activation System on Startup

```python
from fastapi import FastAPI
from app.core_launch import master_activation_controller, activation_conditions

@app.on_event("startup")
async def startup_event():
    """Initialize activation system at startup."""
    
    # Register default modules
    master_activation_controller.register_module("payment_processor")
    master_activation_controller.register_module(
        "banking_connector",
        ["payment_processor"]
    )
    master_activation_controller.register_module(
        "heimdall_core",
        ["banking_connector"]
    )
    master_activation_controller.register_module(
        "property_cloning_engine",
        ["heimdall_core"]
    )
    
    print("✅ Activation system initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    master_activation_controller.disable_master()
    print("🔒 Activation system disabled")
```

### 3. Access Activation in Handlers

```python
from fastapi import APIRouter, Depends
from app.core_launch.master_activation_controller import get_summary

router = APIRouter()

@router.get("/stats")
async def get_stats():
    """Get app stats including activation status."""
    activation_summary = get_summary()
    
    return {
        "status": "ok",
        "activation": {
            "master_enabled": activation_summary["master_enabled"],
            "active_modules": activation_summary["active_modules"],
            "total_modules": activation_summary["total_modules"],
        }
    }
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All activation conditions reviewed
- [ ] Test suite passing (100% coverage)
- [ ] Error handling verified
- [ ] Logging level appropriate
- [ ] Security review completed
- [ ] Database migrations applied
- [ ] Environment variables configured

### Deployment Steps

```bash
# 1. Build and test
pytest tests/test_activation_system.py -v --cov

# 2. Deploy code
# ... your deployment process ...

# 3. Verify endpoints available
curl -s http://localhost:4000/api/v1/activation/status | jq .

# 4. Check logs
docker logs -f app

# 5. Initialize (if manual)
curl -X POST http://localhost:4000/api/v1/activation/debug/register-modules
```

### Post-Deployment

- [ ] Endpoints responding correctly
- [ ] Logging working
- [ ] Metrics being tracked
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team notified

---

## Environment Configuration

### Required Environment Variables

```bash
# .env.production
VALHALLA_ACTIVATION_ENABLED=true
VALHALLA_MASTER_INITIAL_STATE=disabled
VALHALLA_AUTO_REGISTER_MODULES=true
VALHALLA_LOG_LEVEL=INFO
```

### Configuration Class

```python
from pydantic import BaseSettings

class ActivationConfig(BaseSettings):
    """Activation system configuration."""
    
    enabled: bool = True
    master_initial_state: str = "disabled"  # "enabled" or "disabled"
    auto_register_modules: bool = True
    log_level: str = "INFO"
    max_log_entries: int = 10000  # Rotation limit
    
    class Config:
        env_prefix = "VALHALLA_ACTIVATION_"

# Usage
config = ActivationConfig()
```

---

## Monitoring & Alerting

### Prometheus Metrics

```python
from prometheus_client import Counter, Gauge, Histogram

activation_attempts = Counter(
    'valhalla_activation_attempts_total',
    'Total activation attempts',
    ['module', 'result']
)

active_modules = Gauge(
    'valhalla_active_modules',
    'Number of active modules'
)

activation_duration = Histogram(
    'valhalla_activation_duration_seconds',
    'Activation process duration',
    ['module']
)

# Usage
activation_attempts.labels(module='payment_processor', result='success').inc()
active_modules.set(3)
```

### Alert Rules

```yaml
# prometheus-rules.yml
groups:
  - name: valhalla_activation
    rules:
      # Master not enabled when expected
      - alert: ActivationMasterDisabled
        expr: valhalla_activation_master_enabled == 0
        for: 5m
        annotations:
          summary: "Master activation disabled"
      
      # Critical module not active
      - alert: CriticalModuleInactive
        expr: valhalla_active_modules < 2
        for: 2m
        annotations:
          summary: "Critical modules not active"
      
      # High failure rate
      - alert: ActivationFailureRate
        expr: |
          rate(valhalla_activation_attempts_total{result="failed"}[5m]) > 0.1
        annotations:
          summary: "High activation failure rate"
```

### Health Check Endpoint

```python
@router.get("/health/activation")
async def activation_health():
    """Health check for activation system."""
    from app.core_launch.master_activation_controller import get_summary
    
    summary = get_summary()
    
    # Determine health status
    if summary['active_modules'] >= 1:
        status = "healthy"
    elif summary['master_enabled']:
        status = "degraded"
    else:
        status = "unknown"
    
    return {
        "status": status,
        "active_modules": summary['active_modules'],
        "total_modules": summary['total_modules'],
    }
```

---

## Troubleshooting in Production

### Scenario 1: Module Won't Activate

```bash
# 1. Check endpoint availability
curl http://localhost:4000/api/v1/activation/status/payment_processor | jq .

# 2. Check conditions
curl http://localhost:4000/api/v1/activation/conditions | jq .

# 3. Check logs
docker logs -f app | grep -i "payment_processor"

# 4. Check metrics
curl http://localhost:4000/api/v1/activation/conditions/get-metric?name=account_balance

# 5. Get full log
curl http://localhost:4000/api/v1/activation/log?limit=100
```

### Scenario 2: Circular Dependencies

```bash
# Identify circular dependency
curl http://localhost:4000/api/v1/activation/status | jq '.modules[] | select(.status=="blocked")'

# Example response:
# {
#   "module": "module_b",
#   "status": "blocked",
#   "message": "Dependencies not met"
# }

# Fix: Redesign dependencies to be linear
```

### Scenario 3: Emergency Deactivation

```bash
# Kill switch - deactivates all
curl -X POST http://localhost:4000/api/v1/activation/emergency/kill-switch

# Verify deactivation
curl http://localhost:4000/api/v1/activation/status
```

---

## Scaling Considerations

### Single Instance

```
Activation Controller (Single)
    ↓
Condition Engine
    ↓
Modules (activate locally)
```

### Multiple Instances (Recommended for Production)

```
Load Balancer
    ↓
┌─────────────────────────────────┐
│ Instance 1                      │
│ ├─ Activation Controller        │
│ └─ Active Modules               │
├─────────────────────────────────┤
│ Instance 2                      │
│ ├─ Activation Controller        │
│ └─ Active Modules               │
├─────────────────────────────────┤
│ Redis Cache                     │
│ ├─ Shared State                 │
│ └─ Distributed Lock             │
└─────────────────────────────────┘
```

### Distributed Activation

```python
import redis
from typing import Dict, Any

class DistributedActivationController:
    """Activation controller with distributed state."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_shared_state(self) -> Dict[str, Any]:
        """Get activation state from Redis."""
        state = self.redis.get("valhalla:activation:state")
        if state:
            return json.loads(state)
        return {}
    
    async def set_shared_state(self, state: Dict[str, Any]) -> None:
        """Set activation state in Redis."""
        self.redis.set(
            "valhalla:activation:state",
            json.dumps(state)
        )
    
    async def acquire_lock(self, module_name: str, timeout: int = 30) -> bool:
        """Acquire distributed lock for module activation."""
        return self.redis.set(
            f"valhalla:lock:{module_name}",
            "locked",
            ex=timeout,
            nx=True
        )
    
    async def release_lock(self, module_name: str) -> None:
        """Release distributed lock."""
        self.redis.delete(f"valhalla:lock:{module_name}")
```

---

## Backup & Recovery

### Backing Up Activation State

```python
import json
from datetime import datetime

async def backup_activation_state(backup_dir: str):
    """Backup current activation state."""
    from app.core_launch.master_activation_controller import get_summary
    
    state = get_summary()
    
    timestamp = datetime.utcnow().isoformat()
    filename = f"{backup_dir}/activation_backup_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(state, f, indent=2)
    
    return filename
```

### Restoring Activation State

```python
async def restore_activation_state(backup_file: str):
    """Restore activation state from backup."""
    from app.core_launch.master_activation_controller import (
        _activation_controller
    )
    
    with open(backup_file, 'r') as f:
        state = json.load(f)
    
    # Restore modules
    for module_name in state['modules']:
        _activation_controller.register_module(module_name)
    
    print(f"✅ Restored {len(state['modules'])} modules from backup")
```

---

## GitOps Integration

### Example: Helm Values

```yaml
# values.yaml
activation:
  enabled: true
  masterInitialState: disabled
  modules:
    - name: payment_processor
      enabled: true
      replicas: 2
    - name: banking_connector
      enabled: true
      dependencies:
        - payment_processor
    - name: heimdall_core
      enabled: true
      dependencies:
        - banking_connector
```

### Example: Kustomize Patch

```yaml
# kustomization.yaml
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: api
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: VALHALLA_ACTIVATION_ENABLED
          value: "true"
```

---

## Incident Response

### When Master is Disabled

```
Detection     → Alert fires
              ↓
Investigation → Check logs, status
              ↓
Decision      → Was it intentional?
              ↓
Action        → Re-enable or investigate
```

### Playbook: Activation System Down

1. **Assess Impact**
   - Which modules are affected?
   - What's the business impact?

2. **Check Logs**
   ```bash
   docker logs -f app | grep -i activation
   ```

3. **Verify Components**
   ```bash
   # Check Redis (if distributed)
   redis-cli get valhalla:activation:state
   
   # Check database
   SELECT * FROM activation_log ORDER BY timestamp DESC LIMIT 10
   ```

4. **Restart if Needed**
   ```bash
   docker restart app
   ```

5. **Verify Recovery**
   ```bash
   curl http://localhost:4000/api/v1/activation/status
   ```

6. **Post-Mortem**
   - Document what happened
   - Root cause analysis
   - Preventive measures

---

## Cost Optimization

### Reducing Activation Overhead

1. **Cache Condition Results**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128, typed=True)
   def check_condition_cached(condition_name: str) -> bool:
       return check_condition(condition_name)
   ```

2. **Batch Status Checks**
   ```python
   # Instead of checking each module individually
   # Batch into single query
   summary = get_summary()  # Gets all at once
   ```

3. **Lazy Condition Loading**
   ```python
   def get_conditions_lazy(module_name: str):
       # Only load conditions for this module
       # Not all conditions
   ```

---

## Security Hardening

### API Security

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthenticationCredentials

security = HTTPBearer()
router = APIRouter(prefix="/api/v1/activation")

async def verify_admin(credentials: HTTPAuthenticationCredentials = Depends(security)):
    """Verify admin token."""
    if credentials.credentials != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    return True

@router.post("/activate/{module_name}")
async def activate_module(
    module_name: str,
    admin: bool = Depends(verify_admin)
):
    """Admin-only endpoint."""
    # ... activation logic ...
```

### Audit Logging

```python
import logging

audit_logger = logging.getLogger("valhalla.audit")

def log_activation_event(
    event_type: str,
    module_name: str,
    user: str,
    result: str,
    details: dict
):
    """Log activation event for audit."""
    audit_logger.info(
        f"Activation event",
        extra={
            "event_type": event_type,
            "module": module_name,
            "user": user,
            "result": result,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
```

---

## Support & Resources

- **Documentation**: See `ACTIVATION_SYSTEM_GUIDE.md`
- **Quick Reference**: See `ACTIVATION_QUICK_REFERENCE.md`
- **Tests**: `tests/test_activation_system.py`
- **Examples**: `activation_test.py` (interactive test script)

---

**Last Updated**: 2024
**Version**: 1.0
**Status**: Production Ready
