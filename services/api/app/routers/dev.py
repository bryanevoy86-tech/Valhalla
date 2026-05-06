"""Development/Admin endpoints for testing and maintenance."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter(prefix="/api/dev", tags=["Development"])


@router.post("/seed-va-test-data")
def seed_test_data(db: Session = Depends(get_db)):
    """
    Create seed test data for VA Intake system.
    
    ADMIN ONLY - Creates 5 sample leads with varying scores for testing.
    
    Returns:
    - List of created leads with IDs
    - Any errors during creation
    """
    
    from app.services.seed_data import seed_test_data as seed_service
    
    # TODO: Add authentication check to ensure admin
    
    result = seed_service(db)
    
    return result


@router.post("/clear-test-data")
def clear_test_data(db: Session = Depends(get_db)):
    """
    Delete all test seed data.
    
    ADMIN ONLY - Removes all leads created by seed process.
    Be careful with this!
    
    Returns:
    - Number of leads deleted
    """
    
    from app.services.seed_data import clear_seed_data
    
    # TODO: Add authentication check to ensure admin
    
    result = clear_seed_data(db)
    
    return result


@router.get("/duplicate-check")
def check_duplicate_example(db: Session = Depends(get_db)):
    """
    Test the duplicate detection service.
    
    Example endpoint showing how duplicate detection works.
    """
    
    from app.services.duplicate_detection import detect_duplicate_lead
    
    test_data = {
        "address": "123 Main Street",
        "seller_phone": "555-0123",
        "seller_email": "test@example.com",
        "raw_text": "Test property description"
    }
    
    result = detect_duplicate_lead(
        db,
        test_data["address"],
        test_data["seller_phone"],
        test_data["seller_email"],
        test_data["raw_text"]
    )
    
    return {
        "success": True,
        "test": "Duplicate detection check",
        "query": test_data,
        "result": result.to_dict()
    }
