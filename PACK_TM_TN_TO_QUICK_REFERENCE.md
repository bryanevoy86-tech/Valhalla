# PACK TM, TN, TO - Quick Reference

**Status**: ✅ **COMPLETE**  
**Migration**: 0067

---

## 🎯 What's New

### PACK TM: Core Philosophy Archive
Store pillars, values, mission, and non-negotiable rules

**Tables**: 2  
**API Prefix**: `/philosophy`  
**Key Endpoints**:
- `POST /philosophy/records` - Create philosophy record
- `POST /philosophy/principles` - Create principle
- `GET /philosophy/snapshot` - Get latest + all principles

---

### PACK TN: Trust & Relationship Mapping
Map relationships and track trust changes over time

**Tables**: 2  
**API Prefix**: `/relationships`  
**Key Endpoints**:
- `POST /relationships/profiles` - Create profile
- `POST /relationships/events` - Log trust event
- `GET /relationships/snapshot` - Get profiles + events

---

### PACK TO: Daily Rhythm & Tempo Engine
Define daily schedule and Heimdall intensity rules

**Tables**: 2  
**API Prefix**: `/rhythm`  
**Key Endpoints**:
- `POST /rhythm/profiles` - Create rhythm profile
- `POST /rhythm/tempo-rules` - Create tempo rule
- `GET /rhythm/snapshot` - Get profile + rules

---

## 📂 File Locations

### Models
```
services/api/app/models/
  ├── philosophy.py
  ├── relationships.py
  └── daily_rhythm.py
```

### Schemas
```
services/api/app/schemas/
  ├── philosophy.py
  ├── relationships.py
  └── daily_rhythm.py
```

### Services
```
services/api/app/services/
  ├── philosophy.py
  ├── relationships.py
  └── daily_rhythm.py
```

### Routers
```
services/api/app/routers/
  ├── philosophy.py
  ├── relationships.py
  └── daily_rhythm.py
```

### Tests
```
services/api/app/tests/
  ├── test_philosophy.py
  ├── test_relationships.py
  └── test_daily_rhythm.py
```

### Migration
```
services/api/alembic/versions/
  └── 0067_pack_tm_tn_to.py
```

---

## 🚀 Deployment

```powershell
# Apply migration
cd services/api
alembic upgrade head

# Run tests
pytest app/tests/test_philosophy.py -v
pytest app/tests/test_relationships.py -v
pytest app/tests/test_daily_rhythm.py -v

# Start app
python main.py
```

---

## 📊 Database Tables

| Pack | Table | Columns | Purpose |
|------|-------|---------|---------|
| TM | philosophy_records | 10 | Core philosophy docs |
| TM | empire_principles | 5 | Operational principles |
| TN | relationship_profiles | 7 | Relationship info |
| TN | trust_event_logs | 7 | Trust event history |
| TO | daily_rhythm_profiles | 10 | Daily schedule |
| TO | tempo_rules | 6 | Intensity rules |

---

## 🌐 API Endpoints

### Philosophy (/philosophy)
```
POST   /records              Create record
GET    /records              List records
POST   /principles           Create principle
GET    /principles           List principles
GET    /snapshot             Latest record + principles
```

### Relationships (/relationships)
```
POST   /profiles             Create profile
GET    /profiles             List profiles
POST   /events               Create event
GET    /events               List events
GET    /snapshot             Profiles + events
```

### Daily Rhythm (/rhythm)
```
POST   /profiles             Create profile
GET    /profiles             List profiles
POST   /tempo-rules          Create rule
GET    /tempo-rules          List rules (with filter)
GET    /snapshot             Profile + rules
```

---

## 📋 Main.py Updates

**Added Imports**:
```python
from app.routers.philosophy import router as philosophy_router
from app.routers.relationships import router as relationships_router
from app.routers.daily_rhythm import router as daily_rhythm_router
```

**Added Includes**:
```python
app.include_router(philosophy_router)
app.include_router(relationships_router)
app.include_router(daily_rhythm_router)
```

---

## 🔄 Cascade Delete

`relationship_profiles` → `trust_event_logs`

Deleting a relationship profile automatically removes all related trust events.

---

## ✅ Validation Checklist

- [x] 6 tables created
- [x] 3 routers created
- [x] 3 models created
- [x] 3 schemas created
- [x] 3 services created
- [x] 3 test files created
- [x] 1 migration created
- [x] main.py updated
- [x] All imports added
- [x] All routers registered
- [x] Syntax validated
- [x] Ready for deployment

---

## 🛠️ Testing

```bash
# Create philosophy
POST /philosophy/records
{
  "title": "Core Values",
  "mission_statement": "Build lasting empire"
}

# Create relationship
POST /relationships/profiles
{
  "name": "Accountant Bob",
  "role": "professional",
  "user_trust_level": 7.5
}

# Create daily rhythm
POST /rhythm/profiles
{
  "name": "default",
  "wake_time": "07:00",
  "sleep_time": "23:00"
}
```

---

## 📈 Component Count

| Type | Count |
|------|-------|
| Tables | 6 |
| Routers | 3 |
| Models | 3 |
| Schemas | 3 |
| Services | 3 |
| Tests | 3 |
| Endpoints | 15 |
| Test Cases | 21 |

---

## 💾 Migration

- **Revision**: 0067
- **Previous**: 0066
- **Tables**: 6 new
- **Default Values**: 3 set
- **Foreign Keys**: 1 configured
- **Cascade Delete**: 1 enabled

---

## 🎯 Ready for Production

✅ All components created  
✅ All tests written  
✅ Migration file ready  
✅ Main.py updated  
✅ Syntax validated  
✅ Zero breaking changes

**Status**: Ready for immediate deployment
