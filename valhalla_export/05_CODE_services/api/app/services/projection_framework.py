"""
PACK SH: Multi-Year Projection Snapshot Framework
Service functions for scenarios, yearly projections, and variance tracking
"""
from sqlalchemy.orm import Session
from app.models.projection_framework import (
    ProjectionScenario, ProjectionYear, ProjectionVariance, ProjectionReport
)
from datetime import datetime
from typing import List, Optional, Dict, Any


def create_scenario(
    db: Session,
    scenario_id: str,
    name: str,
    created_by: Optional[str] = None,
    description: Optional[str] = None,
    assumptions: Optional[Dict[str, Any]] = None
) -> ProjectionScenario:
    """Create a new projection scenario."""
    scenario = ProjectionScenario(
        scenario_id=scenario_id,
        name=name,
        description=description,
        created_by=created_by,
        assumptions=assumptions
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def get_scenario(db: Session, scenario_id: int) -> Optional[ProjectionScenario]:
    """Get a scenario by ID."""
    return db.query(ProjectionScenario).filter(ProjectionScenario.id == scenario_id).first()


def list_scenarios(db: Session) -> List[ProjectionScenario]:
    """List all projection scenarios."""
    return db.query(ProjectionScenario).all()


def add_projection_year(
    db: Session,
    scenario_id: int,
    year: int,
    expected_income: int,
    expected_expenses: int,
    expected_savings: int,
    expected_cashflow: int,
    expected_net_worth: int,
    notes: Optional[str] = None
) -> ProjectionYear:
    """Add a yearly projection to a scenario."""
    proj_year = ProjectionYear(
        scenario_id=scenario_id,
        year=year,
        expected_income=expected_income,
        expected_expenses=expected_expenses,
        expected_savings=expected_savings,
        expected_cashflow=expected_cashflow,
        expected_net_worth=expected_net_worth,
        notes=notes
    )
    db.add(proj_year)
    db.commit()
    db.refresh(proj_year)
    return proj_year


def get_projection_year(db: Session, scenario_id: int, year: int) -> Optional[ProjectionYear]:
    """Get a yearly projection for a scenario."""
    return db.query(ProjectionYear).filter(
        ProjectionYear.scenario_id == scenario_id,
        ProjectionYear.year == year
    ).first()


def list_projection_years(db: Session, scenario_id: int) -> List[ProjectionYear]:
    """List all yearly projections for a scenario."""
    return db.query(ProjectionYear).filter(ProjectionYear.scenario_id == scenario_id).all()


def record_variance(
    db: Session,
    variance_id: str,
    scenario_id: int,
    year: int,
    metric: str,
    expected: int,
    actual: int,
    explanation: Optional[str] = None
) -> ProjectionVariance:
    """Record actual vs expected variance for a year and metric."""
    difference = actual - expected
    difference_percent = (difference / expected * 100) if expected != 0 else 0

    variance = ProjectionVariance(
        variance_id=variance_id,
        scenario_id=scenario_id,
        year=year,
        metric=metric,
        expected=expected,
        actual=actual,
        difference=difference,
        difference_percent=difference_percent,
        explanation=explanation
    )
    db.add(variance)
    db.commit()
    db.refresh(variance)
    return variance


def get_variance(db: Session, variance_id: str) -> Optional[ProjectionVariance]:
    """Get a variance record by ID."""
    return db.query(ProjectionVariance).filter(ProjectionVariance.variance_id == variance_id).first()


def list_variances_by_scenario_year(
    db: Session,
    scenario_id: int,
    year: int
) -> List[ProjectionVariance]:
    """Get all variance records for a scenario year."""
    return db.query(ProjectionVariance).filter(
        ProjectionVariance.scenario_id == scenario_id,
        ProjectionVariance.year == year
    ).all()


def calculate_scenario_variance_summary(
    db: Session,
    scenario_id: int,
    year: int
) -> Dict[str, Any]:
    """Calculate overall variance summary for a year."""
    variances = list_variances_by_scenario_year(db, scenario_id, year)
    
    if not variances:
        return {"year": year, "metrics": []}

    total_expected = sum(v.expected for v in variances)
    total_actual = sum(v.actual for v in variances)
    total_difference = total_actual - total_expected

    return {
        "year": year,
        "metrics": [
            {
                "metric": v.metric,
                "expected": v.expected,
                "actual": v.actual,
                "difference": v.difference,
                "difference_percent": v.difference_percent
            } for v in variances
        ],
        "total_expected": total_expected,
        "total_actual": total_actual,
        "total_difference": total_difference
    }


def create_projection_report(
    db: Session,
    report_id: str,
    scenario_id: int,
    summary: Optional[Dict[str, Any]] = None,
    narrative: Optional[str] = None,
    notes: Optional[str] = None
) -> ProjectionReport:
    """Create a compiled projection report."""
    report = ProjectionReport(
        report_id=report_id,
        scenario_id=scenario_id,
        generated_at=datetime.utcnow(),
        summary=summary,
        narrative=narrative,
        notes=notes
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_projection_report(db: Session, report_id: str) -> Optional[ProjectionReport]:
    """Get a projection report by ID."""
    return db.query(ProjectionReport).filter(ProjectionReport.report_id == report_id).first()


def list_reports_by_scenario(db: Session, scenario_id: int) -> List[ProjectionReport]:
    """Get all reports for a scenario."""
    return db.query(ProjectionReport).filter(ProjectionReport.scenario_id == scenario_id).all()
