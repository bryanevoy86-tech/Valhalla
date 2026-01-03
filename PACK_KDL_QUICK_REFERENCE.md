# P-KDL Three-Pack Quick Reference

## Knowledge Ingestion (`/core/know/*`)

### Create Document
```bash
curl -X POST http://localhost:5000/core/know/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Policy Document",
    "source": "manual",
    "tags": ["policy", "important"],
    "content": "Full text content here...",
    "linked": {"deal_id": "d123"},
    "meta": {}
  }'
```

### Search Knowledge
```bash
# Search with default settings (10 results)
curl "http://localhost:5000/core/know/search?q=revenue+split"

# Search with limit and tag filter
curl "http://localhost:5000/core/know/search?q=term&limit=20&tag=policy"
```

### List Documents
```bash
# All docs
curl "http://localhost:5000/core/know/docs"

# By tag
curl "http://localhost:5000/core/know/docs?tag=policy"
```

### Get Chunk
```bash
curl "http://localhost:5000/core/know/chunks/chk_abc123"
```

### Rebuild Index
```bash
curl -X POST http://localhost:5000/core/know/rebuild_index
```

### Process Inbox Files
```bash
# Ingest up to 25 files from inbox/
curl -X POST "http://localhost:5000/core/know/ingest_inbox?limit=25"
```

---

## Document Vault (`/core/docs/*`)

### Upload File
```bash
curl -X POST http://localhost:5000/core/docs/upload \
  -F "file=@contract.pdf" \
  -F "tags=contract,deal" \
  -F "linked_json={\"deal_id\": \"d123\"}"
```

### List Documents
```bash
# All docs
curl "http://localhost:5000/core/docs/"

# By tag
curl "http://localhost:5000/core/docs/?tag=contract"

# By link
curl "http://localhost:5000/core/docs/?linked_key=deal_id&linked_val=d123"
```

### Get Document Metadata
```bash
curl "http://localhost:5000/core/docs/doc_abc123"
```

### Download File
```bash
curl "http://localhost:5000/core/docs/doc_abc123/download" > file.pdf
```

### Update Tags
```bash
curl -X POST http://localhost:5000/core/docs/doc_abc123/tags \
  -H "Content-Type: application/json" \
  -d '{
    "add": ["important"],
    "remove": ["draft"]
  }'
```

### Update Links
```bash
# Replace links
curl -X POST http://localhost:5000/core/docs/doc_abc123/link \
  -H "Content-Type: application/json" \
  -d '{
    "linked": {"deal_id": "d456", "loan_id": "l789"},
    "merge": false
  }'

# Merge with existing
curl -X POST http://localhost:5000/core/docs/doc_abc123/link \
  -H "Content-Type: application/json" \
  -d '{
    "linked": {"contact_id": "c123"},
    "merge": true
  }'
```

### Export Metadata
```bash
curl "http://localhost:5000/core/docs/export/metadata" > all_docs.json
```

---

## Legal-Aware Filter (`/core/legal/*`)

### Create Jurisdiction
```bash
curl -X POST http://localhost:5000/core/legal/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "country": "CA",
    "region": "ON",
    "name": "Ontario",
    "notes": "Ontario small business rules"
  }'
```

### List Jurisdictions
```bash
# All profiles
curl "http://localhost:5000/core/legal/profiles"

# By country
curl "http://localhost:5000/core/legal/profiles?country=CA"

# By region
curl "http://localhost:5000/core/legal/profiles?region=ON"
```

### Create Rule
```bash
curl -X POST http://localhost:5000/core/legal/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Equity Threshold",
    "description": "Warn if deal has <20% equity",
    "country": "CA",
    "region": "ON",
    "severity": "warn",
    "action_hint": "Require additional due diligence",
    "conditions": [
      {
        "field": "equity_percent",
        "op": "in",
        "value": [0, 5, 10, 15]
      },
      {
        "field": "deal_type",
        "op": "eq",
        "value": "equity_deal"
      }
    ]
  }'
```

### List Rules
```bash
# All rules
curl "http://localhost:5000/core/legal/rules"

# By country
curl "http://localhost:5000/core/legal/rules?country=CA"

# By region
curl "http://localhost:5000/core/legal/rules?country=US&region=TX"
```

### Evaluate Deal
```bash
curl -X POST http://localhost:5000/core/legal/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "country": "CA",
    "region": "ON",
    "equity_percent": 15,
    "deal_type": "equity_deal",
    "amount_usd": 500000
  }'

# Response:
{
  "ok": true,
  "country": "CA",
  "region": "ON",
  "flags": [
    {
      "rule_id": "lr_xyz",
      "name": "Equity Threshold",
      "severity": "warn",
      "reason": "Rule 'Equity Threshold' triggered",
      "action_hint": "Require additional due diligence"
    }
  ],
  "blocked": false,
  "summary": "Caution: 1 rule(s) triggered."
}
```

---

## Condition Operators (P-LEGAL-1)

| Op | Meaning | Example |
|----|---------| --------|
| `eq` | Equals | `{"field": "status", "op": "eq", "value": "active"}` |
| `neq` | Not equals | `{"field": "status", "op": "neq", "value": "rejected"}` |
| `in` | In list | `{"field": "deal_type", "op": "in", "value": ["equity", "debt"]}` |
| `nin` | Not in list | `{"field": "region", "op": "nin", "value": ["ON", "BC"]}` |
| `exists` | Field exists | `{"field": "loan_id", "op": "exists"}` |
| `truthy` | Field is truthy | `{"field": "verified", "op": "truthy"}` |
| `falsy` | Field is falsy | `{"field": "approved", "op": "falsy"}` |
| `contains` | String/list contains | `{"field": "tags", "op": "contains", "value": "urgent"}` |

---

## Data Location

```
backend/data/
├── know/
│   ├── docs.json        # Document metadata
│   ├── chunks.json      # Text chunks
│   ├── index.json       # Inverted term index
│   ├── inbox/           # File drop directory
│   └── clean/           # Processed files
├── vault/
│   ├── index.json       # Document metadata
│   └── files/           # File storage
└── legal/
    ├── profiles.json    # Jurisdictions
    └── rules.json       # Rules
```

---

## Integration Examples

### Cross-Link Documents to Deal
```bash
# Upload contract linked to deal
curl -X POST http://localhost:5000/core/docs/upload \
  -F "file=@contract.pdf" \
  -F "linked_json={\"deal_id\": \"d123\"}"

# Ingest deal knowledge
curl -X POST http://localhost:5000/core/know/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deal D123 Notes",
    "source": "deal_d123",
    "tags": ["deal"],
    "content": "..."
  }'
```

### Evaluate Deal Against Rules
```bash
# Get deal from system
# → Format as legal context
# → POST to /core/legal/evaluate
# → Check flags (especially severity=block)
# → Apply action_hint
```

### Search Knowledge for Deal Context
```bash
curl "http://localhost:5000/core/know/search?q=equity+structure&tag=deal"
# → Returns chunks with scores
# → Use top hits for deal decision context
```
