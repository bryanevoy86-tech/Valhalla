"""
PACK SH: Multi-Year Projection Snapshot Framework
FastAPI router for projection scenarios and variance tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.projection_framework import (
    ProjectionScenarioSchema, ProjectionYearSchema, ProjectionVarianceSchema,
    ProjectionReportSchema, ScenarioComparisonResponse
)
from app.services import projection_framework
from datetime import datetime

router = APIRouter(prefix="/projections", tags=["PACK SH: Multi-Year Projections"])


@router.post("/scenarios", response_model=ProjectionScenarioSchema)
def create_scenario(
    scenario: ProjectionScenarioSchema,
    db: Session = Depends(get_db)
):
    """Create a new projection scenario."""
    created = projection_framework.create_scenario(
        db,
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        created_by=scenario.created_by,
        description=scenario.description,
        assumptions=scenario.assumptions.dict() if scenario.assumptions else None
    )
    return created


@router.get("/scenarios", response_model=list[ProjectionScenarioSchema])
def list_scenarios(db: Session = Depends(get_db)):
    """List all projection scenarios."""
    scenarios = projection_framework.list_scenarios(db)
    return scenarios


@router.get("/scenarios/{scenario_id}", response_model=ProjectionScenarioSchema)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Get a scenario by ID."""
    scenario = projection_framework.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("/scenarios/{scenario_id}/years", response_model=ProjectionYearSchema)
def add_year(
    scenario_id: int,
    year_data: ProjectionYearSchema,
    db: Session = Depends(get_db)
):
    """Add a yearly projection to a scenario."""
    scenario = projection_framework.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    created = projection_framework.add_projection_year(
        db,
        scenario_id=scenario_id,
        year=year_data.year,
        expected_income=year_data.expected_income,
        expected_expenses=year_data.expected_expenses,
        expected_savings=year_data.expected_savings,
        expected_cashflow=year_data.expected_cashflow,
        expected_net_worth=year_data.expected_net_worth,
        notes=year_data.notes
    )
    return created


@router.get("/scenarios/{scenario_id}/years", response_model=list[ProjectionYearSchema])
def list_years(scenario_id: int, db: Session = Depends(get_db)):
    """List all yearly projections for a scenario."""
    scenario = projection_framework.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    years = projection_framework.list_projection_years(db, scenario_id)
    return years


@router.get("/scenarios/{scenario_id}/years/{year}")
def get_year(scenario_id: int, year: int, db: Session = Depends(get_db)):
    """Get a specific year's projection."""
    proj_year = projection_framework.get_projection_year(db, scenario_id, year)
    if not proj_year:
        raise HTTPException(status_code=404, detail="Projection year not found")
    return proj_year


@router.post("/variances", response_model=ProjectionVarianceSchema)
def record_variance(
    variance: ProjectionVarianceSchema,
    db: Session = Depends(get_db)
):
    """Record actual vs expected variance for a year."""
    created = projection_framework.record_variance(
        db,
        variance_id=variance.variance_id,
        scenario_id=variance.scenario_id,
        year=variance.year,
        metric=variance.metric,
        expected=variance.expected,
        actual=variance.actual,
        explanation=variance.explanation
    )
    return created


@router.get("/variances/{scenario_id}/{year}")
def get_variances(scenario_id: int, year: int, db: Session = Depends(get_db)):
    """Get all variance records for a scenario year."""
    variances = projection_framework.list_variances_by_scenario_year(db, scenario_id, year)
    return variances


@router.get("/summary/{scenario_id}/{year}")
def variance_summary(scenario_id: int, year: int, db: Session = Depends(get_db)):
    """Get variance summary for a scenario year."""
    summary = projection_framework.calculate_scenario_variance_summary(db, scenario_id, year)
    return summary


@router.post("/reports", response_model=ProjectionReportSchema)
def create_report(
    report: ProjectionReportSchema,
    db: Session = Depends(get_db)
):
    """Create a compiled projection report."""
    created = projection_framework.create_projection_report(
        db,
        report_id=report.report_id,
        scenario_id=report.scenario_id,
        summary=report.summary,
        narrative=report.narrative,
        notes=report.notes
    )
    return created


@router.get("/reports/{report_id}", response_model=ProjectionReportSchema)
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Get a projection report by ID."""
    report = projection_framework.get_projection_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/reports/scenario/{scenario_id}")
def get_scenario_reports(scenario_id: int, db: Session = Depends(get_db)):
    """Get all reports for a scenario."""
    reports = projection_framework.list_reports_by_scenario(db, scenario_id)
    return reports


@router.get("/comparison/{scenario_id}", response_model=ScenarioComparisonResponse)
def scenario_comparison(scenario_id: int, db: Session = Depends(get_db)):
    """Get comparison summary for a scenario."""
    scenario = projection_framework.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    years = projection_framework.list_projection_years(db, scenario_id)
    
    total_expected_income = sum(y.expected_income for y in years)
    total_expected_expenses = sum(y.expected_expenses for y in years)

    return ScenarioComparisonResponse(
        scenario_name=scenario.name,
        years_included=len(years),
        total_expected_income=total_expected_income,
        total_expected_expenses=total_expected_expenses
    )
