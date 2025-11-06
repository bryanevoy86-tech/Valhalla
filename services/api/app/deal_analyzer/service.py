"""
Service logic for Automated Deal Analyzer (Pack 34).
AI-driven analysis of real estate deals for profitability and risk assessment.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.deal_analyzer.models import DealAnalysis
from app.deal_analyzer.schemas import DealAnalysisCreate, DealMetrics


def analyze_and_create_deal(db: Session, deal: DealAnalysisCreate) -> DealAnalysis:
    """
    Analyze a deal and store the results.
    Calculates ROI, profitability, risk score, and AI recommendation.
    """
    # Calculate metrics
    metrics = calculate_deal_metrics(
        purchase_price=deal.purchase_price,
        rehab_cost=deal.rehab_cost,
        arv=deal.arv
    )
    
    # Generate AI recommendation
    recommendation = generate_ai_recommendation(metrics)
    
    # Generate analysis notes
    notes = f"Total investment: ${metrics.total_investment:,.2f}. "
    notes += f"Expected profit: ${metrics.expected_profit:,.2f}. "
    notes += f"Risk score: {metrics.risk_score:.1f}/100. "
    notes += f"Recommendation: {recommendation.upper()}"
    
    db_deal = DealAnalysis(
        property_address=deal.property_address,
        purchase_price=deal.purchase_price,
        rehab_cost=deal.rehab_cost,
        arv=deal.arv,
        expected_profit=metrics.expected_profit,
        roi=metrics.roi_percentage,
        cash_on_cash_return=metrics.cash_on_cash_return,
        is_profitable=metrics.is_profitable,
        risk_score=metrics.risk_score,
        ai_recommendation=recommendation,
        analysis_notes=notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal


def get_all_analyses(db: Session, skip: int = 0, limit: int = 100) -> list[DealAnalysis]:
    """Retrieve all deal analyses with pagination."""
    return db.query(DealAnalysis).order_by(DealAnalysis.roi.desc()).offset(skip).limit(limit).all()


def get_analysis_by_id(db: Session, analysis_id: int) -> DealAnalysis | None:
    """Get a specific deal analysis by ID."""
    return db.query(DealAnalysis).filter(DealAnalysis.id == analysis_id).first()


def get_profitable_deals(db: Session, min_roi: float = 0.0) -> list[DealAnalysis]:
    """Filter deals by profitability and minimum ROI."""
    return (
        db.query(DealAnalysis)
        .filter(DealAnalysis.is_profitable == True)
        .filter(DealAnalysis.roi >= min_roi)
        .order_by(DealAnalysis.roi.desc())
        .all()
    )


def get_deals_by_recommendation(db: Session, recommendation: str) -> list[DealAnalysis]:
    """Filter deals by AI recommendation (pass, review, reject)."""
    return (
        db.query(DealAnalysis)
        .filter(DealAnalysis.ai_recommendation == recommendation)
        .order_by(DealAnalysis.roi.desc())
        .all()
    )


def calculate_deal_metrics(purchase_price: float, rehab_cost: float, arv: float) -> DealMetrics:
    """
    Calculate comprehensive deal metrics using standard real estate formulas.
    
    Formulas:
    - Total Investment = Purchase Price + Rehab Cost
    - Expected Profit = ARV - Total Investment
    - ROI % = (Expected Profit / Total Investment) * 100
    - Profit Margin % = (Expected Profit / ARV) * 100
    """
    total_investment = purchase_price + rehab_cost
    expected_profit = arv - total_investment
    roi_percentage = (expected_profit / total_investment * 100) if total_investment > 0 else 0
    profit_margin = (expected_profit / arv * 100) if arv > 0 else 0
    is_profitable = expected_profit > 0
    
    # Calculate cash-on-cash return (simplified; assumes 20% down payment)
    down_payment = purchase_price * 0.20
    total_cash = down_payment + rehab_cost
    cash_on_cash = (expected_profit / total_cash * 100) if total_cash > 0 else None
    
    # Calculate risk score (0-100, higher = riskier)
    risk_score = calculate_risk_score(roi_percentage, profit_margin, total_investment, arv)
    
    # Generate recommendation
    if roi_percentage >= 25 and risk_score < 30:
        recommendation = "pass"
    elif roi_percentage >= 15 and risk_score < 50:
        recommendation = "review"
    else:
        recommendation = "reject"
    
    return DealMetrics(
        total_investment=total_investment,
        expected_profit=expected_profit,
        roi_percentage=roi_percentage,
        cash_on_cash_return=cash_on_cash,
        profit_margin=profit_margin,
        is_profitable=is_profitable,
        risk_score=risk_score,
        recommendation=recommendation
    )


def calculate_risk_score(roi: float, margin: float, investment: float, arv: float) -> float:
    """
    Calculate deal risk score (0-100).
    Factors: ROI, profit margin, investment size, ARV accuracy estimate.
    Lower score = lower risk.
    """
    risk = 50.0  # baseline
    
    # ROI risk: lower ROI = higher risk
    if roi < 10:
        risk += 20
    elif roi < 20:
        risk += 10
    elif roi >= 30:
        risk -= 15
    
    # Margin risk: thin margins = higher risk
    if margin < 10:
        risk += 15
    elif margin >= 20:
        risk -= 10
    
    # Investment size risk: very large deals = slightly higher risk
    if investment > 500000:
        risk += 5
    
    # ARV ratio risk: purchase price too close to ARV = risky
    purchase_ratio = (investment / arv) if arv > 0 else 1
    if purchase_ratio > 0.85:
        risk += 15
    elif purchase_ratio < 0.65:
        risk -= 10
    
    return max(0.0, min(100.0, risk))  # clamp to 0-100


def generate_ai_recommendation(metrics: DealMetrics) -> str:
    """
    AI-driven recommendation based on calculated metrics.
    Returns: 'pass', 'review', or 'reject'
    """
    if metrics.roi_percentage >= 25 and metrics.risk_score < 30 and metrics.is_profitable:
        return "pass"
    elif metrics.roi_percentage >= 15 and metrics.risk_score < 50 and metrics.is_profitable:
        return "review"
    else:
        return "reject"
