# PACK Deployment Quick Reference

## 3 New PACK Systems Deployed - January 2, 2026

### Overview

| PACK | Name | Purpose | Status |
|---|---|---|---|
| **P-LEGAL-1** | Legal-Aware Deal Filter | Jurisdiction rulesets (allowed/flagged/blocked) | ✅ Live |
| **P-PARTNER-1** | Partner/JV Management | Registry + dashboard + notes | ✅ Live |
| **P-KNOW-3** | Knowledge Links + Citations | Entity source linking + formatted citations | ✅ Live |

---

## Quick Start

### 1. Legal Filter - Check a Deal

```python
# Seed defaults (one time)
POST /core/legal/seed_defaults
```

```python
# Run check
POST /core/legal/check
{
  "jurisdiction_key": "CA:MB",
  "subject": "deal",
  "mode": "execute",
  "cone_band": "B",
  "payload": {
    "strategy": "wholesale",
    "seller": {"id_verified": false}
  }
}

Response:
{
  "overall": "flagged",           # allowed | flagged | blocked
  "findings": [                   # triggered rules
    {
      "rule_id": "mb_assignment_disclosure",
      "outcome": "flagged",
      "severity": "medium",
      "message": "...",
      "next_actions": ["Use templates...", "Confirm..."]
    }
  ],
  "next_actions": ["..."]
}
```

**Jurisdictions:** CA:MB, US:FL (extensible)  
**Mode:** explore (soft) or execute (hard blocks)  
**Cone Band:** A/B (risky hint for C/D bands)

---

### 2. Partners - Create & View

```python
# Create partner
POST /core/partners
{
  "name": "John JV",
  "partner_type": "jv_partner",    # jv_partner | buyer | lender | contractor | agent | vendor | other
  "status": "active",               # active | paused | archived
  "tier": "A",                      # A | B | C | D
  "location": "Winnipeg, MB",
  "tags": ["wholesale", "manitoba"]
}

Response: {"id": "pt_abc123", "name": "John JV", ...}
```

```python
# Add note to partner
POST /core/partners/notes
{
  "partner_id": "pt_abc123",
  "title": "Q1 Planning Call",
  "body": "Discussed return structure...",
  "visibility": "internal"         # internal | shareable
}

Response: {"id": "pn_xyz789", "title": "...", ...}
```

```python
# Get dashboard
GET /core/partners/dashboard

Response:
{
  "totals": {"partners": 5, "notes": 12},
  "by_type": {"jv_partner": 3, "buyer": 2},
  "recent_partners": [...8 latest...],
  "recent_notes": [...10 latest...]
}
```

---

### 3. Knowledge - Link & Cite

```python
# Attach sources to any entity
POST /core/knowledge/attach
{
  "entity_type": "partner",        # deal | partner | doc | tx | obligation | property | other
  "entity_id": "pt_abc123",
  "sources": [
    {
      "source_type": "note",       # doc | url | note | chat | file | other
      "ref": "pn_xyz789",
      "title": "Q1 Call",
      "snippet": "10-15% return"
    }
  ],
  "tags": ["jv", "active"]
}

Response: {"id": "kl_def456", "sources": [...], "tags": [...]}
```

```python
# Format citations
POST /core/knowledge/citations/format
{
  "style": "short",                # short | long
  "sources": [
    {
      "source_type": "note",
      "ref": "pn_xyz789",
      "title": "Q1 Call",
      "snippet": "10-15% return"
    }
  ]
}

Response:
{
  "citations": [
    "[S1] Q1 Call:pn_xyz789"                              # short
    # OR
    "[S1] Q1 Call — note:pn_xyz789 — 10-15% return"     # long
  ]
}
```

---

## Data Locations

| System | Store | Path |
|---|---|---|
| **Legal** | profiles.json | `backend/data/legal_filter/` |
| **Partners** | partners.json | `backend/data/partners/` |
| **Partners** | notes.json | `backend/data/partners/` |
| **Knowledge** | links.json | `backend/data/knowledge/` |

All files use **atomic writes** (temp + os.replace).

---

## UUID Prefixes

| Type | Prefix | Example |
|---|---|---|
| Jurisdiction Profile | (key) | CA:MB, US:FL |
| Partner | pt_ | pt_cc32dbb5edfb |
| Partner Note | pn_ | pn_467dcfcee513 |
| Knowledge Link | kl_ | kl_0b4442a79d72 |

---

## Endpoints Reference

### Legal Filter (`/core/legal`)
- `POST /seed_defaults` — Initialize CA:MB, US:FL profiles
- `GET /profiles` — List all jurisdiction profiles
- `GET /profiles/{key}` — Get profile (CA:MB, US:FL)
- `POST /profiles` — Create/update profile
- `POST /check` — Run jurisdiction check

### Partners (`/core/partners`)
- `POST /` — Create partner
- `GET /` — List partners (filters: status, partner_type, tier)
- `GET /{id}` — Get partner
- `PATCH /{id}` — Update partner
- `POST /notes` — Create note
- `GET /notes/list` — List notes (filters: partner_id, visibility)
- `GET /dashboard` — Dashboard summary

### Knowledge (`/core/knowledge`)
- `POST /attach` — Attach sources to entity
- `GET /links` — List links (filters: entity_type, entity_id)
- `POST /citations/format` — Format citation list

---

## Test Suite

**File:** `test_pack_legal_partners_knowledge_unit.py`

Run tests (no server needed):
```bash
python test_pack_legal_partners_knowledge_unit.py
```

**Results:** 12/12 PASSING (100%)
- 4 P-LEGAL-1 tests
- 4 P-PARTNER-1 tests
- 4 P-KNOW-3 tests

---

## Integration Points

### Legal Filter Can Check:
- Deal strategy (wholesale, assignment, retail, etc.)
- Seller/buyer verification status
- Disclosure completeness
- Extensible: add CA:ON, US:TX, etc. and custom rules

### Partners Can Link To:
- Deals (via deal_id in notes)
- Documents (via citation system)
- Transactions (future)

### Knowledge Can Reference:
- Partners (sources/notes)
- Deals (documentation)
- Properties (research)
- Obligations (justification)

---

## Troubleshooting

### Legal check returns 404
**Issue:** Jurisdiction profile not found  
**Fix:** `POST /core/legal/seed_defaults` to initialize CA:MB, US:FL

### Partner note creation fails
**Issue:** Partner ID doesn't exist  
**Fix:** Create partner first: `POST /core/partners`

### Citations format empty
**Issue:** Sources array missing or empty  
**Fix:** Ensure sources array has at least one item with source_type, ref

---

## Performance Notes

- **Profiles:** ~50 rules per jurisdiction (fast evaluation)
- **Partners:** Sorts by tier then name (O(n log n))
- **Knowledge:** Deduplicates by (source_type, ref) tuple
- **Storage:** All JSON files, minimal I/O overhead
- **Scale:** Tested with 2+ profiles, 1+ partners, 1+ notes, 1+ links

---

## Version Info

- **Python:** 3.13+
- **FastAPI:** 0.100+
- **Pydantic:** v2
- **Deployment Date:** January 2, 2026
- **Status:** Production Ready ✅

---

## Support

For detailed documentation, see:
- `PACK_LEGAL_PARTNERS_KNOWLEDGE_DEPLOYMENT.md` — Full deployment guide
- `test_pack_legal_partners_knowledge_unit.py` — Usage examples in tests
