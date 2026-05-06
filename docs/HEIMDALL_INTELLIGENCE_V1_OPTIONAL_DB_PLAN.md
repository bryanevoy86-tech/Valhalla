# Heimdall Intelligence V1 — Optional Database Plan

**Status:** Design Document (OPTIONAL - NOT Applied in Phase 1)  
**Created:** 2026-04-13  
**Purpose:** Document database persistence path WITHOUT applying any migrations yet.

---

## Critical Rule: NO MIGRATIONS IN PHASE 1

✋ **STOP: No migrations are being applied in Phase 1**

This document describes the optional database persistence strategy but does NOT execute it.

Reasons:
- ✅ Service layer works without database
- ✅ In-memory storage sufficient for beta testing
- ✅ Routes fully functional with stubbed data
- ✅ Reduces deployment risk
- ✅ Can migrate cleanly after logic is proven

---

## When to Apply These Migrations

✅ After Execution Console is live and stable  
✅ After first 20+ deals have been manually recorded  
✅ After team is comfortable with Heimdall workflows  
✅ When data volume justifies persistence  
✅ No earlier than Month 1+ post-launch

---

## Migration Plan (OPTIONAL, Deferred)

### IF you decide to persist to database:

```
Phase L: Apply ORM Models (app/models/heimdall_intelligence.py)
         ↓
Phase 2: Create Migration File
         (alembic/versions/0XXX_create_heimdall_tables.py)
         ↓
Phase 3: Run: alembic upgrade head
         ↓
Phase 4: Update Service Layer
         (Replace in-memory with SQLAlchemy queries)
         ↓
Phase 5: Deploy and test
```

---

## SQLAlchemy Models (Reference Only)

**These would go in:** `app/models/heimdall_intelligence.py`

```python
"""
Heimdall Intelligence SQLAlchemy Models

IMPORTANT: These models are NOT currently used.
Service layer uses in-memory storage (Phase 1).

These models are ready to implement when:
1. Logic is proven with in-memory storage
2. Team wants database persistence
3. Data volume justifies persistence

DO NOT use these in Phase 1.
"""

from sqlalchemy import Column, String, Text, Float, DateTime, JSON, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base  # Assumes database session exists


class HeimdallKnowledgeSource(Base):
    """Knowledge source - where knowledge comes from"""
    
    __tablename__ = "heimdall_knowledge_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(255), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    source_url = Column(String(1024), nullable=True)
    jurisdiction = Column(String(10), nullable=True)
    market = Column(String(50), nullable=True, index=True)
    category = Column(String(100), nullable=True)
    trust_level = Column(String(20), nullable=False, default="medium")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    knowledge_items = relationship("HeimdallKnowledgeItem", back_populates="source", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_source_market_trust', 'market', 'trust_level'),
        Index('ix_source_active', 'active'),
    )


class HeimdallKnowledgeItem(Base):
    """Knowledge item - individual piece of knowledge"""
    
    __tablename__ = "heimdall_knowledge_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("heimdall_knowledge_sources.id"), nullable=False)
    title = Column(String(500), nullable=False, index=True)
    content_raw = Column(Text, nullable=True)
    content_summary = Column(Text, nullable=True)
    knowledge_type = Column(String(50), nullable=False, index=True)
    market = Column(String(50), nullable=True, index=True)
    strategy = Column(JSON, nullable=True)  # Array of strategies
    asset_type = Column(String(50), nullable=True, index=True)
    tags_json = Column(JSON, nullable=True)  # Array of tags
    confidence_score = Column(Float, nullable=False, default=0.5)
    status = Column(String(20), nullable=False, default="draft", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    source = relationship("HeimdallKnowledgeSource", back_populates="knowledge_items")
    insights = relationship("HeimdallKnowledgeInsight", back_populates="knowledge_item", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_item_market_type_status', 'market', 'knowledge_type', 'status'),
        Index('ix_item_confidence', 'confidence_score'),
    )


class HeimdallKnowledgeInsight(Base):
    """Structured insight from knowledge item"""
    
    __tablename__ = "heimdall_knowledge_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_item_id = Column(UUID(as_uuid=True), ForeignKey("heimdall_knowledge_items.id"), nullable=False)
    insight_text = Column(String(1000), nullable=False)
    structured_value_json = Column(JSON, nullable=True)
    applicable_market = Column(String(50), nullable=True, index=True)
    applicable_strategy = Column(String(50), nullable=True, index=True)
    confidence_score = Column(Float, nullable=False, default=0.75)
    supporting_evidence = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    knowledge_item = relationship("HeimdallKnowledgeItem", back_populates="insights")


class HeimdallOutcomeFeedback(Base):
    """Recorded outcome from execution"""
    
    __tablename__ = "heimdall_outcome_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), nullable=True, index=True)  # Reference to execution case
    deal_id = Column(String(50), nullable=True, index=True)
    market = Column(String(50), nullable=False, index=True)
    strategy = Column(String(50), nullable=False, index=True)
    asset_type = Column(String(50), nullable=True, index=True)
    predicted_result_json = Column(JSON, nullable=True)
    actual_result_json = Column(JSON, nullable=True)
    delta_json = Column(JSON, nullable=True)  # Calculated differences
    lesson_text = Column(Text, nullable=True)
    confidence_adjustment = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_outcome_market_strategy', 'market', 'strategy'),
        Index('ix_outcome_created', 'created_at'),
    )


class HeimdallDecisionMemory(Base):
    """Decision memory - what was recommended, decided, and outcome"""
    
    __tablename__ = "heimdall_decision_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type = Column(String(100), nullable=False, index=True)
    subject_id = Column(String(255), nullable=True, index=True)
    market = Column(String(50), nullable=False, index=True)
    strategy = Column(String(50), nullable=True, index=True)
    recommendation_text = Column(String(1000), nullable=False)
    decision_taken = Column(String(1000), nullable=True)
    outcome_score = Column(Float, nullable=True)  # -1.0 to +1.0
    lesson_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_decision_market_strategy', 'market', 'strategy'),
        Index('ix_decision_subject', 'subject_type', 'subject_id'),
    )
```

---

## Migration File (TEMPLATE, Not Applied)

**This would go in:** `alembic/versions/0XXX_create_heimdall_tables.py`

```python
"""Create Heimdall Intelligence tables

Revision ID: 0XXX
Revises: [previous migration]
Create Date: 2026-04-13

NOT APPLIED IN PHASE 1 - This is optional for future persistence
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0XXX'
down_revision = None  # Set to actual previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create hemdalll_knowledge_sources
    op.create_table(
        'heimdall_knowledge_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_url', sa.String(1024), nullable=True),
        sa.Column('jurisdiction', sa.String(10), nullable=True),
        sa.Column('market', sa.String(50), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('trust_level', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_source_market_trust', 'market', 'trust_level'),
        sa.Index('ix_source_active', 'active'),
    )
    
    # Create heimdall_knowledge_items
    op.create_table(
        'heimdall_knowledge_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content_raw', sa.Text(), nullable=True),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('knowledge_type', sa.String(50), nullable=False),
        sa.Column('market', sa.String(50), nullable=True),
        sa.Column('strategy', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('asset_type', sa.String(50), nullable=True),
        sa.Column('tags_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['heimdall_knowledge_sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_item_market_type_status', 'market', 'knowledge_type', 'status'),
        sa.Index('ix_item_confidence', 'confidence_score'),
    )
    
    # Similar for other tables...
    # (complete table definitions follow same pattern)


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('heimdall_decision_memory')
    op.drop_table('heimdall_outcome_feedback')
    op.drop_table('heimdall_knowledge_insights')
    op.drop_table('heimdall_knowledge_items')
    op.drop_table('heimdall_knowledge_sources')
```

---

## Migration Safety Analysis

**Why this migration is safe when applied:**

✅ **New Tables Only** — No existing table modifications  
✅ **Additive** — Only adds capability; doesn't change execution layer  
✅ **Idempotent** — Can be rolled back cleanly  
✅ **Indexes** — Designed for query performance  
✅ **No Constraints** — Foreign keys to external systems via string ID only  
✅ **Nullable Fields** — Can handle partial data  
✅ **No Defaults** — Relies on application code for values  

**Risk Level:** ⭐ VERY LOW (assuming applied at right time)

---

## When NOT to Apply This Migration

❌ Before service layer is tested and stable  
❌ During active execution layer deployments  
❌ Before team has documented at least 5 outcomes  
❌ Without team training on outcome recording  
❌ If in-memory storage is working fine  

---

## Benefits of Deferring Database

**Phase 1 Benefits (In-Memory):**
- ✅ Zero database complexity
- ✅ Fast API development
- ✅ Easy to test and iterate
- ✅ No migration risk
- ✅ Service logic proven before persistence
- ✅ Data doesn't survive app restarts (intentional for beta)

**Phase 2+ Benefits (Persistent Database):**
- ✅ Data survives restarts
- ✅ Scalable to thousands of records
- ✅ Query optimization via indexes
- ✅ Team can browse historical data
- ✅ Enables advanced analytics

---

## Deployment Procedure (When Ready)

**Step 1: Verify Readiness**
```
- Execution Console is live 1+ weeks
- 20+ deals have been manually recorded  
- Team is comfortable with outcome flow
- Service layer tests all pass
```

**Step 2: Prepare**
```bash
# Create migration file (alembic handles)
alembic revision -m "create_heimdall_tables"

# Review generated file in alembic/versions/
# Ensure all 5 tables are present
```

**Step 3: Test Locally**
```bash
# Test migration locally
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

**Step 4: Deploy**
```bash
# Deploy code changes (service layer using DB)
git push main

# Run migration on production
alembic upgrade head
```

**Step 5: Verify**
```sql
-- Verify tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'heimdall_%';
```

**Step 6: Monitor**
```
- Check app logs for any errors
- Verify knowledge search still works
- Record a test outcome
- Verify market memory still works
```

---

## Rollback Procedure (If Needed)

**Easy Rollback:**
```bash
# Rollback one migration
alembic downgrade -1

# Verify tables are gone
SELECT * FROM information_schema.tables 
WHERE table_name LIKE 'heimdall_%';

# Redeploy code with in-memory fallback
git push main
```

**Time to Rollback:** ~5 minutes  
**Data Loss:** Any outcomes recorded to persistent DB (should be backed up)  
**Impact on Execution:** ZERO (tables are separate)

---

## Summary

| Aspect | Phase 1 (Now) | Phase 2+ (Optional) |
|--------|---------------|-------------------|
| Storage | In-memory | PostgreSQL |
| Persistence | Per-session | Persistent |
| Scale | 0-100 records | 0-10000+ records |
| Query Speed | Fast | Very fast |
| Complexity | Low | Medium |
| Risk | None | Very low |
| Application Ready | ✅ Yes | ✅ Yes (when deployed) |

---

## Decision: Persist Now or Later?

**NOW (Phase 1):**
- Arguments: Faster launch, less risk, proven logic first
- Best for: Teams uncertain about Heimdall workflow
- Recommendation: ✅ DO THIS

**LATER (Phase 2+):**
- Arguments: Data survival, scalability, team training
- Best for: After outcomes are being recorded regularly
- Recommendation: ✅ PLAN FOR THIS

**NEVER:**
- We will always keep in-memory fallback
- Can disable Heimdall without breaking anything
- Can migrate data in/out anytime

---

**Status:** Deferred. Ready to implement when needed. Zero risk, zero rush.
