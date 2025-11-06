"""
Service logic for AI Behavioral Profiling (Pack 33).
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.behavioral_profiling.models import BehavioralProfile
from app.behavioral_profiling.schemas import BehavioralProfileCreate, BehavioralProfileUpdate, EngagementRecommendation


def create_behavioral_profile(db: Session, profile: BehavioralProfileCreate) -> BehavioralProfile:
    """Create a new behavioral profile."""
    db_profile = BehavioralProfile(
        user_id=profile.user_id,
        lead_id=profile.lead_id,
        behavioral_score=profile.behavioral_score,
        interests=profile.interests,
        engagement_level=profile.engagement_level or _calculate_engagement_level(profile.behavioral_score),
        last_engaged_at=profile.last_engaged_at or datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def get_all_profiles(db: Session, skip: int = 0, limit: int = 100) -> list[BehavioralProfile]:
    """Retrieve all behavioral profiles with pagination."""
    return db.query(BehavioralProfile).offset(skip).limit(limit).all()


def get_profile_by_user(db: Session, user_id: int) -> BehavioralProfile | None:
    """Get behavioral profile for a specific user."""
    return db.query(BehavioralProfile).filter(BehavioralProfile.user_id == user_id).first()


def get_profiles_by_engagement(db: Session, engagement_level: str) -> list[BehavioralProfile]:
    """Filter profiles by engagement level."""
    return db.query(BehavioralProfile).filter(BehavioralProfile.engagement_level == engagement_level).all()


def update_profile(db: Session, profile_id: int, update_data: BehavioralProfileUpdate) -> BehavioralProfile | None:
    """Update an existing behavioral profile."""
    db_profile = db.query(BehavioralProfile).filter(BehavioralProfile.id == profile_id).first()
    if not db_profile:
        return None
    
    if update_data.behavioral_score is not None:
        setattr(db_profile, "behavioral_score", update_data.behavioral_score)
        # Auto-update engagement level based on score
        setattr(db_profile, "engagement_level", _calculate_engagement_level(update_data.behavioral_score))
    
    if update_data.interests is not None:
        setattr(db_profile, "interests", update_data.interests)
    
    if update_data.engagement_level is not None:
        setattr(db_profile, "engagement_level", update_data.engagement_level)
    
    if update_data.last_engaged_at is not None:
        setattr(db_profile, "last_engaged_at", update_data.last_engaged_at)
    
    setattr(db_profile, "updated_at", datetime.utcnow())
    db.commit()
    db.refresh(db_profile)
    return db_profile


def generate_engagement_strategy(db: Session, user_id: int) -> EngagementRecommendation | None:
    """
    AI-driven engagement strategy recommendation based on behavioral profile.
    Returns personalized strategy for maximizing user engagement.
    """
    profile = get_profile_by_user(db, user_id)
    if not profile:
        return None
    
    # Extract values and ensure proper types
    score: float = profile.behavioral_score  # type: ignore
    level: str = profile.engagement_level  # type: ignore
    interests: str = profile.interests or ""  # type: ignore
    
    # Simple AI heuristic for demonstration (can be replaced with ML model)
    if score >= 70:
        strategy = "Maintain engagement with premium content and exclusive offers"
        confidence = 0.9
        reasoning = f"High engagement score ({score}) indicates strong interest. Focus on retention."
    elif score >= 40:
        strategy = "Re-engage with personalized content based on interests: " + interests
        confidence = 0.75
        reasoning = f"Medium engagement ({score}). Tailor content to stated interests."
    else:
        strategy = "Win-back campaign with special incentives and simplified onboarding"
        confidence = 0.6
        reasoning = f"Low engagement ({score}). Needs re-activation with strong value proposition."
    
    return EngagementRecommendation(
        user_id=user_id,
        recommended_strategy=strategy,
        confidence_score=confidence,
        reasoning=reasoning
    )


def _calculate_engagement_level(score: float) -> str:
    """Helper to auto-calculate engagement level from score."""
    if score >= 70:
        return "high"
    elif score >= 40:
        return "medium"
    else:
        return "low"
