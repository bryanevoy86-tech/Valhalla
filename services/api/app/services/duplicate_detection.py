"""Duplicate lead detection service."""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models import VALead


class DuplicateDetectionResult:
    """Result of duplicate detection check."""
    
    def __init__(self):
        self.has_duplicates = False
        self.matches = []
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "duplicate_warning": self.has_duplicates,
            "possible_matches": self.matches
        }


def detect_duplicate_lead(
    db: Session,
    address: str,
    seller_phone: str = None,
    seller_email: str = None,
    raw_text: str = None
) -> DuplicateDetectionResult:
    """
    Check if a lead with similar details already exists.
    
    Checks for:
    - Exact address match
    - Phone number match
    - Email match
    - Similar raw text (contains same key phrases)
    
    Args:
        db: Database session
        address: Property address
        seller_phone: Seller phone number
        seller_email: Seller email
        raw_text: Raw text description
    
    Returns:
        DuplicateDetectionResult with matches
    """
    result = DuplicateDetectionResult()
    
    # Build query for possible duplicates
    conditions = []
    
    # Exact address match (most reliable)
    if address and address.strip():
        address_clean = address.strip().lower()
        exact_address = db.query(VALead).filter(
            VALead.address.ilike(f"%{address_clean}%")
        ).all()
        
        if exact_address:
            result.has_duplicates = True
            for lead in exact_address:
                result.matches.append({
                    "id": lead.id,
                    "reason": "Same address",
                    "address": lead.address,
                    "seller_name": lead.seller_name,
                    "created_at": lead.created_at.isoformat() if lead.created_at else None,
                    "status": lead.status
                })
    
    # Phone number match
    if seller_phone and seller_phone.strip():
        phone_clean = seller_phone.strip()
        phone_matches = db.query(VALead).filter(
            VALead.seller_phone == phone_clean
        ).all()
        
        if phone_matches:
            result.has_duplicates = True
            for lead in phone_matches:
                # Check if already in matches
                existing = any(m["id"] == lead.id for m in result.matches)
                if not existing:
                    result.matches.append({
                        "id": lead.id,
                        "reason": "Same phone number",
                        "address": lead.address,
                        "seller_name": lead.seller_name,
                        "created_at": lead.created_at.isoformat() if lead.created_at else None,
                        "status": lead.status
                    })
    
    # Email match
    if seller_email and seller_email.strip():
        email_clean = seller_email.strip().lower()
        email_matches = db.query(VALead).filter(
            VALead.seller_email.ilike(email_clean)
        ).all()
        
        if email_matches:
            result.has_duplicates = True
            for lead in email_matches:
                # Check if already in matches
                existing = any(m["id"] == lead.id for m in result.matches)
                if not existing:
                    result.matches.append({
                        "id": lead.id,
                        "reason": "Same email address",
                        "address": lead.address,
                        "seller_name": lead.seller_name,
                        "created_at": lead.created_at.isoformat() if lead.created_at else None,
                        "status": lead.status
                    })
    
    # Text similarity (look for key phrases)
    if raw_text and raw_text.strip():
        raw_text_lower = raw_text.strip().lower()
        
        # If text contains strong indicators, check other leads
        if len(raw_text_lower) > 20:
            all_leads = db.query(VALead).all()
            
            for lead in all_leads:
                if not lead.raw_text:
                    continue
                
                lead_text = lead.raw_text.lower()
                
                # Count matching words (simple heuristic)
                raw_words = set(raw_text_lower.split())
                lead_words = set(lead_text.split())
                
                # If they share multiple key words (more than 5 common significant words)
                common_words = raw_words & lead_words
                
                # Filter to significant words (> 3 chars, not common articles)
                common_significant = {w for w in common_words if len(w) > 3 and w not in {"that", "this", "with", "from"}}
                
                if len(common_significant) >= 5:
                    result.has_duplicates = True
                    # Check if already in matches
                    existing = any(m["id"] == lead.id for m in result.matches)
                    if not existing:
                        result.matches.append({
                            "id": lead.id,
                            "reason": "Similar description",
                            "address": lead.address,
                            "seller_name": lead.seller_name,
                            "created_at": lead.created_at.isoformat() if lead.created_at else None,
                            "status": lead.status,
                            "similarity_score": len(common_significant) / len(raw_words) if raw_words else 0
                        })
    
    return result
