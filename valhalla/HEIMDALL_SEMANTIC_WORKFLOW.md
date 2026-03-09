# Heimdall Semantic Search Workflow

## Overview
This document describes how Heimdall uses Valhalla's semantic search capabilities to ground its research and task generation in actual documentation.

---

## Architecture Flow

```
┌─────────────────┐
│  Documentation  │
│   Sources       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ /research/      │  ← Step 1: Ingest raw docs
│ ingest          │     Parses HTML, stores text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ResearchDoc    │  ← Stored in database
│  (raw text)     │     with source metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ External        │  ← Step 2: Compute embeddings
│ Embedding Model │     (OpenAI, Cohere, etc.)
│ (Heimdall)      │     Generate vectors from text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ /embeddings/    │  ← Step 3: Store vectors
│ upsert          │     Link vector to doc_id
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ResearchDoc     │  ← Doc now has embedding_json
│ + embedding     │     Ready for semantic search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Query      │  ← Step 4: Query time
│ "How do I...?"  │     User asks a question
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ External        │  ← Step 5: Embed the query
│ Embedding Model │     Same model as Step 2
│ (Heimdall)      │     Generate query vector
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ /semantic_query │  ← Step 6: Find similar docs
│                 │     Cosine similarity search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ranked Results  │  ← Step 7: Get grounded context
│ {doc_id, score, │     Use in Builder/Playbooks
│  url, preview}  │
└─────────────────┘
```

---

## Step-by-Step Integration

### Step 1: Ingest Documentation

**What it does:** Fetches and parses documentation from enabled sources, stores raw text in database.

**API Call:**
```bash
POST /api/research/ingest
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "url": "https://docs.example.com/guide",
  "source_id": 1
}
```

**Result:** Creates `ResearchDoc` records with:
- `url`, `title`, `body_text`
- `source_id` (links to ResearchSource)
- `embedding_json` = NULL (not yet embedded)

**Automation:** `/jobs/research/ingest_all` runs nightly via GitHub Actions to keep docs fresh.

---

### Step 2: Compute Embeddings (External)

**What it does:** Heimdall takes the raw text and generates vector embeddings using an external model.

**Example (OpenAI):**
```python
import openai

# Get docs that need embeddings
response = requests.get(
    "https://valhalla-api-ha6a.onrender.com/api/research/embeddings/stats",
    headers={"X-API-Key": BUILDER_KEY}
)
stats = response.json()
# stats["without_embeddings"] shows count

# For each doc without embeddings:
doc = get_doc_by_id(doc_id)
embedding_response = openai.Embedding.create(
    input=doc["body_text"],
    model="text-embedding-ada-002"
)
vector = embedding_response["data"][0]["embedding"]  # 1536 dimensions
```

**Example (Cohere):**
```python
import cohere

co = cohere.Client(api_key=COHERE_KEY)
doc = get_doc_by_id(doc_id)
response = co.embed(
    texts=[doc["body_text"]],
    model="embed-english-v3.0"
)
vector = response.embeddings[0]  # 1024 dimensions
```

**Note:** Use the **same model and version** for both document embeddings and query embeddings to ensure vectors are comparable.

---

### Step 3: Store Embeddings

**What it does:** Persists the computed vectors back to Valhalla, linking them to their source docs.

**API Call:**
```bash
POST /api/research/embeddings/upsert
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "doc_id": 123,
  "vector": [0.0234, -0.0567, 0.0891, ..., 0.0123]  # Full dimension array
}
```

**Result:** Updates `research_docs.embedding_json` with the vector. Doc is now searchable.

**Batch Processing:**
```python
# Process all docs needing embeddings
docs_to_embed = get_docs_without_embeddings()

for doc in docs_to_embed:
    vector = compute_embedding(doc["body_text"])
    
    requests.post(
        "https://valhalla-api-ha6a.onrender.com/api/research/embeddings/upsert",
        headers={"X-API-Key": BUILDER_KEY},
        json={"doc_id": doc["id"], "vector": vector}
    )
```

---

### Step 4: User Query

**What it does:** User asks Heimdall a question about their codebase, framework, or domain.

**Example Questions:**
- "How do I set up FastAPI with SQLAlchemy?"
- "Show me examples of React hooks"
- "What's the best practice for error handling?"

**Heimdall's Goal:** Find the most relevant documentation to ground its response.

---

### Step 5: Embed the Query

**What it does:** Convert the user's natural language query into a vector using the **same embedding model** from Step 2.

**Example:**
```python
import openai

query = "How do I set up FastAPI with SQLAlchemy?"

embedding_response = openai.Embedding.create(
    input=query,
    model="text-embedding-ada-002"  # SAME model as doc embeddings
)
query_vector = embedding_response["data"][0]["embedding"]
```

**Critical:** Query and document embeddings **must use the same model** for cosine similarity to be meaningful.

---

### Step 6: Semantic Search

**What it does:** Searches for docs with similar embeddings using cosine similarity, returns top matches ranked by relevance.

**API Call:**
```bash
POST /api/research/semantic_query
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "vector": [0.0234, -0.0567, 0.0891, ..., 0.0123],  # Query embedding
  "top_k": 5,          # Return top 5 matches
  "min_score": 0.7,    # Only results with ≥70% similarity
  "q": "FastAPI SQLAlchemy setup"  # Optional: fallback text search
}
```

**Response:**
```json
{
  "hits": [
    {
      "doc_id": 42,
      "url": "https://fastapi.tiangolo.com/tutorial/sql-databases/",
      "title": "SQL (Relational) Databases - FastAPI",
      "score": 0.89,
      "preview": "FastAPI doesn't require you to use a SQL (relational) database..."
    },
    {
      "doc_id": 87,
      "url": "https://docs.sqlalchemy.org/en/14/orm/tutorial.html",
      "title": "Object Relational Tutorial - SQLAlchemy",
      "score": 0.82,
      "preview": "The SQLAlchemy Object Relational Mapper presents a method..."
    }
  ]
}
```

**Behavior:**
- **If embeddings exist:** Returns ranked by cosine similarity
- **If no embeddings:** Falls back to text search on `body_text` using `q` parameter
- **Hybrid:** Can combine both (vector + text relevance)

---

### Step 7: Ground Builder Tasks

**What it does:** Use the semantic search results to provide context for code generation, playbooks, and task creation.

**Integration with Builder:**

```python
# Heimdall workflow when user asks: "Create a FastAPI endpoint for users"

# 1. Embed the query
query_vector = embed_query("Create a FastAPI endpoint for users")

# 2. Search relevant docs
search_results = semantic_query(query_vector, top_k=3)

# 3. Extract context
context_urls = [hit["url"] for hit in search_results["hits"]]
context_previews = [hit["preview"] for hit in search_results["hits"]]

# 4. Pass to Builder
task_payload = {
    "description": "Create a FastAPI endpoint for users",
    "context": {
        "relevant_docs": context_urls,
        "doc_previews": context_previews,
        "confidence_scores": [hit["score"] for hit in search_results["hits"]]
    }
}

response = requests.post(
    "https://valhalla-api-ha6a.onrender.com/api/builder/tasks",
    headers={"X-API-Key": BUILDER_KEY},
    json=task_payload
)
```

**Benefits:**
- Builder generates code based on actual documentation patterns
- Reduces hallucinations by grounding in real examples
- Provides source citations for transparency
- Learns from project-specific conventions over time

---

## Monitoring & Maintenance

### Check Embedding Coverage

**API Call:**
```bash
GET /api/research/embeddings/stats
X-API-Key: <BUILDER_KEY>
```

**Response:**
```json
{
  "total_docs": 150,
  "with_embeddings": 120,
  "without_embeddings": 30,
  "coverage_percent": 80.0
}
```

**Action:** If coverage < 100%, run embedding generation for remaining docs.

---

### Refresh Embeddings

When documentation updates:

1. **Re-ingest:** Call `/research/ingest` for updated URL
2. **Re-embed:** Compute new embedding for updated `body_text`
3. **Upsert:** Overwrite old embedding with new vector

**Example:**
```bash
# Step 1: Re-ingest updated doc
POST /api/research/ingest
{
  "url": "https://docs.example.com/updated-guide",
  "source_id": 1
}

# Step 2: Get updated doc_id from response
# Step 3: Compute new embedding externally
# Step 4: Upsert new vector
POST /api/research/embeddings/upsert
{
  "doc_id": 42,
  "vector": [<new_embedding>]
}
```

---

## Example End-to-End Flow

### Scenario: User asks "How do I add authentication to FastAPI?"

```python
# 1. Heimdall receives question
user_query = "How do I add authentication to FastAPI?"

# 2. Embed query (OpenAI example)
query_embedding = openai.Embedding.create(
    input=user_query,
    model="text-embedding-ada-002"
)["data"][0]["embedding"]

# 3. Search Valhalla's research docs
search_response = requests.post(
    "https://valhalla-api-ha6a.onrender.com/api/research/semantic_query",
    headers={"X-API-Key": BUILDER_KEY},
    json={
        "vector": query_embedding,
        "top_k": 5,
        "min_score": 0.6
    }
)

hits = search_response.json()["hits"]

# 4. Build grounded response
context = "\n\n".join([
    f"Source: {hit['title']} ({hit['url']})\n{hit['preview']}"
    for hit in hits
])

heimdall_response = f"""
Based on the following documentation:

{context}

Here's how to add authentication to FastAPI:

1. Install dependencies: `pip install python-jose[cryptography] passlib[bcrypt]`
2. Create authentication utilities...
[Generated code based on doc patterns]

References:
{chr(10).join([f"- {hit['title']}: {hit['url']}" for hit in hits])}
"""

# 5. If user asks to implement it, create Builder task
if user_confirms_implementation:
    task_response = requests.post(
        "https://valhalla-api-ha6a.onrender.com/api/builder/tasks",
        headers={"X-API-Key": BUILDER_KEY},
        json={
            "description": "Add JWT authentication to FastAPI app",
            "context": {
                "relevant_docs": [hit["url"] for hit in hits],
                "confidence_scores": [hit["score"] for hit in hits]
            }
        }
    )
```

---

## Best Practices

### 1. Embedding Model Selection

- **Use consistent models:** Same model for docs and queries
- **Consider dimensions:** More dimensions = more nuance (but slower/costlier)
  - OpenAI ada-002: 1536 dims, good balance
  - Cohere v3.0: 1024 dims, efficient
  - Sentence-BERT: 384-768 dims, free but lower quality

### 2. Batch Processing

- **Embed in batches:** Most providers support batch API calls
- **Rate limiting:** Respect provider rate limits
- **Cost optimization:** Cache embeddings, avoid re-embedding unchanged docs

### 3. Search Tuning

- **`top_k`:** Start with 3-5, increase for broader context
- **`min_score`:** 
  - 0.5-0.6: Loose matching (exploratory)
  - 0.7-0.8: Moderate matching (balanced)
  - 0.8+: Strict matching (high precision)
- **Fallback:** Always provide `q` parameter for text search backup

### 4. Monitoring

- **Track coverage:** Keep embeddings at >90% of docs
- **Monitor scores:** If all results <0.5, embeddings may be stale
- **A/B test:** Compare semantic vs text search quality

---

## Next Steps

1. **Choose Embedding Model:** OpenAI, Cohere, or self-hosted
2. **Build Embedding Pipeline:** Script to process all ingested docs
3. **Integrate with Heimdall:** Add semantic search to query flow
4. **Monitor & Iterate:** Track search quality, adjust parameters
5. **Automate Refresh:** Schedule re-embedding for updated docs

---

## API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/research/ingest` | POST | Ingest new documentation |
| `/research/embeddings/upsert` | POST | Store/update doc embedding |
| `/research/semantic_query` | POST | Search by vector similarity |
| `/research/embeddings/stats` | GET | Check embedding coverage |
| `/jobs/research/ingest_all` | POST | Batch ingest all enabled sources |

All endpoints require `X-API-Key: <BUILDER_KEY>` header.

---

## Troubleshooting

**Issue:** Search returns no results
- **Check:** Embedding coverage (`/embeddings/stats`)
- **Fix:** Ensure docs have embeddings via `/upsert`

**Issue:** Low similarity scores (<0.5)
- **Check:** Using same embedding model for query and docs?
- **Fix:** Re-embed with consistent model

**Issue:** Slow queries
- **Check:** Database has index on `research_docs.id`
- **Fix:** Already handled by SQLAlchemy primary key

**Issue:** Out-of-date results
- **Check:** When were docs last ingested?
- **Fix:** Re-run `/ingest` or nightly job

---

## Related Documentation

- [RESEARCH_CORE_SETUP.md](./RESEARCH_CORE_SETUP.md) - Initial research system setup
- [research_semantic.py](./services/api/app/routers/research_semantic.py) - Implementation details
- [v3_4_embeddings.py](./services/api/alembic/versions/v3_4_embeddings.py) - Database schema

---

**Last Updated:** November 2, 2025
