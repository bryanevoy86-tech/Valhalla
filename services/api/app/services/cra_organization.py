"""Services for PACK SF: CRA / Tax Interaction Organizational Module"""

from sqlalchemy.orm import Session
from app.models.cra_organization import (
    CRADocument, CRASummary, CRACategoryMap, FiscalYearSnapshot
)
from app.schemas.cra_organization import (
    CRADocumentSchema, CRASummarySchema, CRACategoryMapSchema, FiscalYearSnapshotSchema
)
from datetime import datetime
from typing import List, Optional


# ========== CRA DOCUMENT VAULT FUNCTIONS ==========

def create_cra_document(db: Session, doc_data: CRADocumentSchema) -> CRADocument:
    """Create CRA document vault entry"""
    db_doc = CRADocument(**doc_data.model_dump())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


def get_cra_document(db: Session, doc_id: int) -> Optional[CRADocument]:
    """Get document by ID"""
    return db.query(CRADocument).filter(CRADocument.id == doc_id).first()


def get_documents_by_year(db: Session, year: int) -> List[CRADocument]:
    """Get all documents for tax year"""
    return db.query(CRADocument).filter(CRADocument.year == year).all()


def get_documents_by_category(db: Session, year: int, category: str) -> List[CRADocument]:
    """Get documents by category"""
    return db.query(CRADocument).filter(
        CRADocument.year == year,
        CRADocument.category == category
    ).all()


def flag_document(db: Session, doc_id: int, reason: str) -> CRADocument:
    """Flag document for review"""
    doc = get_cra_document(db, doc_id)
    if doc:
        doc.flagged = True
        doc.flag_reason = reason
        doc.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)
    return doc


# ========== CRA SUMMARY FUNCTIONS ==========

def create_annual_summary(db: Session, summary_data: CRASummarySchema) -> CRASummary:
    """Create annual CRA summary"""
    db_summary = CRASummary(**summary_data.model_dump())
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary


def get_annual_summary(db: Session, year: int) -> Optional[CRASummary]:
    """Get annual summary for year"""
    return db.query(CRASummary).filter(CRASummary.year == year).first()


def update_summary_status(db: Session, summary_id: int, status: str) -> CRASummary:
    """Update summary review status"""
    summary = db.query(CRASummary).filter(CRASummary.id == summary_id).first()
    if summary:
        summary.review_status = status  # pending, reviewed, filed
        summary.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(summary)
    return summary


def add_flagged_item(db: Session, summary_id: int, item: dict) -> CRASummary:
    """Add flagged item to summary"""
    summary = db.query(CRASummary).filter(CRASummary.id == summary_id).first()
    if summary:
        if not summary.flagged_items:
            summary.flagged_items = []
        summary.flagged_items.append(item)
        summary.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(summary)
    return summary


def add_accountant_question(db: Session, summary_id: int, question: dict) -> CRASummary:
    """Add question for accountant"""
    summary = db.query(CRASummary).filter(CRASummary.id == summary_id).first()
    if summary:
        if not summary.questions_for_accountant:
            summary.questions_for_accountant = []
        summary.questions_for_accountant.append(question)
        summary.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(summary)
    return summary


# ========== CATEGORY MAP FUNCTIONS ==========

def create_category_map(db: Session, map_data: CRACategoryMapSchema) -> CRACategoryMap:
    """Create category mapping"""
    db_map = CRACategoryMap(**map_data.model_dump())
    db.add(db_map)
    db.commit()
    db.refresh(db_map)
    return db_map


def get_category_map(db: Session, category: str) -> Optional[CRACategoryMap]:
    """Get mapping for category"""
    return db.query(CRACategoryMap).filter(CRACategoryMap.category == category).first()


def list_category_maps(db: Session) -> List[CRACategoryMap]:
    """List all category mappings"""
    return db.query(CRACategoryMap).all()


def add_example_transaction(db: Session, map_id: int, example: dict) -> CRACategoryMap:
    """Add example transaction to category"""
    cat_map = db.query(CRACategoryMap).filter(CRACategoryMap.id == map_id).first()
    if cat_map:
        if not cat_map.example_transactions:
            cat_map.example_transactions = []
        cat_map.example_transactions.append(example)
        cat_map.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cat_map)
    return cat_map


# ========== FISCAL YEAR SNAPSHOT FUNCTIONS ==========

def create_fiscal_snapshot(db: Session, snapshot_data: FiscalYearSnapshotSchema) -> FiscalYearSnapshot:
    """Create fiscal year snapshot"""
    db_snapshot = FiscalYearSnapshot(**snapshot_data.model_dump())
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def get_fiscal_snapshot(db: Session, year: int) -> Optional[FiscalYearSnapshot]:
    """Get fiscal year snapshot"""
    return db.query(FiscalYearSnapshot).filter(FiscalYearSnapshot.year == year).first()


def get_completeness_score(db: Session, year: int) -> float:
    """
    Calculate completeness score (0-100) based on documentation and flagged items.
    Safe calculation - not tax-related.
    """
    documents = db.query(CRADocument).filter(CRADocument.year == year).all()
    summary = get_annual_summary(db, year)
    
    if not documents or not summary:
        return 0.0
    
    # Metrics for completeness
    doc_count = len(documents)
    flagged_count = len([d for d in documents if d.flagged])
    gaps_count = len(summary.documentation_gaps) if summary.documentation_gaps else 0
    
    # Calculate score (higher doc count, lower flags = better)
    base_score = min(100, (doc_count / 10) * 100)  # Max at 10 docs per category
    flag_penalty = flagged_count * 5  # Each flag reduces by 5
    gap_penalty = gaps_count * 10  # Each gap reduces by 10
    
    score = max(0, base_score - flag_penalty - gap_penalty)
    return score


def get_annual_report(db: Session, year: int) -> dict:
    """
    Get comprehensive annual report for review.
    Organizes all data - no tax interpretation.
    """
    summary = get_annual_summary(db, year)
    documents = get_documents_by_year(db, year)
    snapshot = get_fiscal_snapshot(db, year)
    
    completeness = get_completeness_score(db, year)
    
    return {
        "year": year,
        "summary": summary,
        "total_documents": len(documents),
        "documents_by_category": _group_by_category(documents),
        "flagged_items_count": sum(1 for d in documents if d.flagged),
        "snapshot": snapshot,
        "completeness_score": completeness,
        "questions_for_accountant": summary.questions_for_accountant if summary else []
    }


def _group_by_category(documents: List[CRADocument]) -> dict:
    """Helper: group documents by category"""
    grouped = {}
    for doc in documents:
        if doc.category not in grouped:
            grouped[doc.category] = []
        grouped[doc.category].append(doc)
    return grouped
