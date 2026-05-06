"""Seed test data for VA Intake system."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import VALead
from app.services.heimdall_lead_intake import score_lead, build_lead_record


SEED_LEADS = [
    {
        "source_platform": "facebook",
        "source_type": "manual_va",
        "address": "123 Oak Street",
        "city": "Toronto",
        "province": "ON",
        "seller_name": "John Smith",
        "seller_phone": "416-555-0101",
        "seller_email": "john@example.com",
        "asking_price": 450000,
        "raw_text": "Need to sell quickly. House needs work. Estate sale. Behind on payments.",
    },
    {
        "source_platform": "website",
        "source_type": "manual_va",
        "address": "456 Maple Avenue",
        "city": "Vancouver",
        "province": "BC",
        "seller_name": "Sarah Johnson",
        "seller_phone": "604-555-0202",
        "seller_email": "sarah@example.com",
        "asking_price": 750000,
        "raw_text": "Vacant property. As-is condition. Motivated seller. Quick possession available.",
    },
    {
        "source_platform": "referral",
        "source_type": "manual_va",
        "address": "789 Pine Road",
        "city": "Calgary",
        "province": "AB",
        "seller_name": "Mike Wilson",
        "seller_phone": "403-555-0303",
        "seller_email": "mike@example.com",
        "asking_price": 350000,
        "raw_text": "Fire damage. Property needs extensive repairs. Landlord tired of management.",
    },
    {
        "source_platform": "facebook",
        "source_type": "manual_va",
        "address": "321 Elm Drive",
        "city": "Montreal",
        "province": "QC",
        "seller_name": "Lisa Chen",
        "seller_phone": "514-555-0404",
        "seller_email": "lisa@example.com",
        "asking_price": 550000,
        "raw_text": "Fixer-upper. Water damage in basement. Estate property. Motivated to sell.",
    },
    {
        "source_platform": "website",
        "source_type": "manual_va",
        "address": "654 Cedar Lane",
        "city": "Edmonton",
        "province": "AB",
        "seller_name": "Robert Brown",
        "seller_phone": "780-555-0505",
        "seller_email": "robert@example.com",
        "asking_price": 320000,
        "raw_text": "Tenant problems. Handyman special. As-is sale. Foreclosure situation.",
    },
]


def seed_test_data(db: Session) -> dict:
    """
    Create seed test data for development/testing.
    
    ADMIN ONLY - This should only be called by admin users.
    
    Args:
        db: Database session
    
    Returns:
        dict with seed results
    """
    
    created_leads = []
    errors = []
    
    for seed in SEED_LEADS:
        try:
            # Score the lead
            analysis = score_lead(seed)
            
            # Build lead record
            lead_dict = build_lead_record(seed, analysis)
            lead_dict["submitted_by"] = "seed_test_data"
            
            # Create lead
            lead = VALead(**lead_dict)
            db.add(lead)
            db.flush()  # Flush to get the ID
            
            created_leads.append({
                "id": lead.id,
                "address": lead.address,
                "score": lead.heimdall_score,
                "status": lead.status
            })
            
        except Exception as e:
            errors.append({
                "address": seed.get("address"),
                "error": str(e)
            })
    
    # Commit all
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Failed to commit: {str(e)}",
            "created": len(created_leads),
            "failed": len(errors)
        }
    
    return {
        "success": True,
        "message": f"Created {len(created_leads)} test leads",
        "created_leads": created_leads,
        "errors": errors if errors else None,
        "note": "Test data created. Use GET /api/va-intake/leads to view all leads."
    }


def clear_seed_data(db: Session) -> dict:
    """
    Delete all test seed data.
    
    ADMIN ONLY - Be careful with this!
    
    Args:
        db: Database session
    
    Returns:
        dict with clear results
    """
    
    try:
        # Find leads submitted by seed process
        seed_leads = db.query(VALead).filter(
            VALead.submitted_by == "seed_test_data"
        ).all()
        
        count = len(seed_leads)
        for lead in seed_leads:
            db.delete(lead)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Deleted {count} test leads",
            "deleted": count
        }
    
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
