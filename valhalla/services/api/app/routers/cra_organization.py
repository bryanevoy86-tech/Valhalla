"""Router for PACK SF: CRA / Tax Interaction Organizational Module"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.schemas.cra_organization import (
    CRADocumentSchema, CRASummarySchema, CRACategoryMapSchema,
    FiscalYearSnapshotSchema, CRAAnnualReportResponse
)
from app.services import cra_organization

router = APIRouter(prefix="/cra", tags=["PACK SF: CRA Organization"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== CRA DOCUMENT VAULT ENDPOINTS ==========

@router.post("/documents", response_model=CRADocumentSchema)
def create_cra_document(doc: CRADocumentSchema, db: Session = Depends(get_db)):
    """Create document in CRA vault"""
    return cra_organization.create_cra_document(db, doc)


@router.get("/documents/{year}", response_model=list[CRADocumentSchema])
def get_documents_by_year(year: int, db: Session = Depends(get_db)):
    """Get all documents for tax year"""
    return cra_organization.get_documents_by_year(db, year)


@router.get("/documents/{year}/{category}", response_model=list[CRADocumentSchema])
def get_documents_by_category(year: int, category: str, db: Session = Depends(get_db)):
    """Get documents by category"""
    return cra_organization.get_documents_by_category(db, year, category)


@router.patch("/documents/{doc_id}/flag")
def flag_cra_document(doc_id: int, reason: str, db: Session = Depends(get_db)):
    """Flag document for review"""
    doc = cra_organization.get_cra_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return cra_organization.flag_document(db, doc_id, reason)


# ========== CRA SUMMARY ENDPOINTS ==========

@router.post("/summary", response_model=CRASummarySchema)
def create_annual_summary(summary: CRASummarySchema, db: Session = Depends(get_db)):
    """Create annual CRA summary"""
    return cra_organization.create_annual_summary(db, summary)


@router.get("/summary/{year}", response_model=CRASummarySchema)
def get_annual_summary(year: int, db: Session = Depends(get_db)):
    """Get annual summary for year"""
    summary = cra_organization.get_annual_summary(db, year)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for year")
    
    return summary


@router.patch("/summary/{summary_id}/status")
def update_summary_status(summary_id: int, status: str, db: Session = Depends(get_db)):
    """Update summary review status (pending, reviewed, filed)"""
    return cra_organization.update_summary_status(db, summary_id, status)


@router.post("/summary/{summary_id}/flag-item")
def add_flagged_item(summary_id: int, item: dict, db: Session = Depends(get_db)):
    """Add flagged item to summary"""
    return cra_organization.add_flagged_item(db, summary_id, item)


@router.post("/summary/{summary_id}/question")
def add_accountant_question(summary_id: int, question: dict, db: Session = Depends(get_db)):
    """Add question for accountant"""
    return cra_organization.add_accountant_question(db, summary_id, question)


# ========== CATEGORY MAP ENDPOINTS ==========

@router.post("/categories", response_model=CRACategoryMapSchema)
def create_category_map(cat_map: CRACategoryMapSchema, db: Session = Depends(get_db)):
    """Create category mapping"""
    return cra_organization.create_category_map(db, cat_map)


@router.get("/categories", response_model=list[CRACategoryMapSchema])
def list_category_maps(db: Session = Depends(get_db)):
    """List all category mappings"""
    return cra_organization.list_category_maps(db)


@router.get("/categories/{category}", response_model=CRACategoryMapSchema)
def get_category_map(category: str, db: Session = Depends(get_db)):
    """Get mapping for category"""
    cat_map = cra_organization.get_category_map(db, category)
    if not cat_map:
        raise HTTPException(status_code=404, detail="Category mapping not found")
    
    return cat_map


@router.post("/categories/{map_id}/example")
def add_example_transaction(map_id: int, example: dict, db: Session = Depends(get_db)):
    """Add example transaction to category"""
    return cra_organization.add_example_transaction(db, map_id, example)


# ========== FISCAL YEAR SNAPSHOT ENDPOINTS ==========

@router.post("/snapshot", response_model=FiscalYearSnapshotSchema)
def create_fiscal_snapshot(snapshot: FiscalYearSnapshotSchema, db: Session = Depends(get_db)):
    """Create fiscal year snapshot"""
    return cra_organization.create_fiscal_snapshot(db, snapshot)


@router.get("/snapshot/{year}", response_model=FiscalYearSnapshotSchema)
def get_fiscal_snapshot(year: int, db: Session = Depends(get_db)):
    """Get fiscal year snapshot"""
    snapshot = cra_organization.get_fiscal_snapshot(db, year)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found for year")
    
    return snapshot


# ========== ANNUAL REPORT ENDPOINTS ==========

@router.get("/report/{year}", response_model=CRAAnnualReportResponse)
def get_annual_report(year: int, db: Session = Depends(get_db)):
    """Get comprehensive annual CRA report"""
    report_data = cra_organization.get_annual_report(db, year)
    
    if not report_data["summary"]:
        raise HTTPException(status_code=404, detail="No summary found for year")
    
    summary = report_data["summary"]
    completeness = report_data["completeness_score"]
    
    return CRAAnnualReportResponse(
        year=year,
        summary=summary,
        documents_count=report_data["total_documents"],
        flagged_items_count=report_data["flagged_items_count"],
        unusual_items_count=len(summary.unusual_transactions) if summary.unusual_transactions else 0,
        gaps_count=len(summary.documentation_gaps) if summary.documentation_gaps else 0,
        questions_for_accountant_count=len(summary.questions_for_accountant) if summary.questions_for_accountant else 0,
        completeness_score=completeness,
        ready_for_filing=summary.review_status == "reviewed" and completeness > 70
    )
