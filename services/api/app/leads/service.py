"""
Lead service logic for Advanced Lead Scraper (Pack 31).

Handles lead creation, retrieval, and status updates aligned with canonical schema.
Includes input sanitization and validation to prevent malformed data.
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.leads.models import Lead
from app.leads.schemas import LeadCreate
from app.core.sanitization import sanitize_input, sanitize_string_field
from app.core.error_logging import APIErrorLogger

logger = logging.getLogger(__name__)


def sanitize_lead_data(lead: LeadCreate) -> dict:
    """
    Sanitize all string fields in lead data.
    
    Args:
        lead: LeadCreate schema instance
    
    Returns:
        Dictionary with sanitized lead data
    """
    lead_dict = lead.model_dump()
    
    sanitized = {
        "lead_name": sanitize_string_field(lead_dict.get("lead_name"), "Unknown"),
        "lead_email": lead_dict.get("lead_email"),  # Email validated by Pydantic
        "lead_phone": sanitize_input(lead_dict.get("lead_phone")),
        "property_address": sanitize_string_field(lead_dict.get("property_address")),
        "property_city": sanitize_string_field(lead_dict.get("property_city")),
        "property_state": sanitize_string_field(lead_dict.get("property_state")),
        "property_zip": sanitize_string_field(lead_dict.get("property_zip")),
        "estimated_arv": lead_dict.get("estimated_arv"),  # Numeric, pass through
        "source": sanitize_string_field(lead_dict.get("source"), "unknown"),
        "lead_status": sanitize_string_field(lead_dict.get("lead_status"), "new"),
        "notes": sanitize_string_field(lead_dict.get("notes")),
    }
    
    return sanitized


def validate_lead_data(lead_data: dict) -> tuple[bool, str | None]:
    """
    Validate lead data after sanitization.
    
    Args:
        lead_data: Sanitized lead data dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = ["lead_name", "lead_email", "lead_phone", "source"]
    
    for field in required_fields:
        value = lead_data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            error_msg = f"Required field '{field}' is missing or empty"
            logger.warning(f"Lead validation failed: {error_msg}")
            return False, error_msg
    
    # Validate lead name length
    if len(lead_data.get("lead_name", "")) < 2:
        return False, "Lead name must be at least 2 characters"
    
    # Validate phone number (basic check)
    phone = lead_data.get("lead_phone", "")
    if len(phone) < 10:
        return False, "Phone number must be at least 10 characters"
    
    # Validate estimated_arv if provided
    if lead_data.get("estimated_arv") is not None:
        try:
            arv = float(lead_data["estimated_arv"])
            if arv < 0:
                return False, "Estimated ARV cannot be negative"
        except (TypeError, ValueError):
            return False, "Estimated ARV must be a valid number"
    
    # Validate lead status
    valid_statuses = ["new", "contacted", "qualified", "working", "closed", "lost"]
    if lead_data.get("lead_status") not in valid_statuses:
        return False, f"Invalid lead status. Must be one of: {', '.join(valid_statuses)}"
    
    return True, None


def create_lead(db: Session, lead: LeadCreate) -> Lead:
    """
    Create a new lead with contact and property information.
    Includes input sanitization and validation.
    
    Args:
        db: Database session
        lead: Lead data from request
    
    Returns:
        Created Lead model instance
    
    Raises:
        ValueError: If validation fails
    """
    try:
        # Log incoming request
        logger.info(f"Creating lead: {lead.lead_name} from {lead.source}")
        APIErrorLogger.log_request_payload(
            endpoint="/leads",
            payload=lead.model_dump(exclude={"lead_email", "lead_phone"})  # Don't log PII
        )
        
        # Sanitize all fields
        original_data = lead.model_dump()
        sanitized_data = sanitize_lead_data(lead)
        
        # Log sanitization changes
        for field, original_value in original_data.items():
            if original_value != sanitized_data.get(field):
                APIErrorLogger.log_sanitization(
                    endpoint="/leads",
                    field=field,
                    original=original_value,
                    sanitized=sanitized_data.get(field)
                )
        
        # Validate sanitized data
        is_valid, error_msg = validate_lead_data(sanitized_data)
        if not is_valid:
            APIErrorLogger.log_validation_error(
                endpoint="/leads",
                field="lead_data",
                error_message=error_msg
            )
            raise ValueError(error_msg)
        
        # Create lead in database
        db_lead = Lead(
            lead_name=sanitized_data["lead_name"],
            lead_email=sanitized_data["lead_email"],
            lead_phone=sanitized_data["lead_phone"],
            property_address=sanitized_data["property_address"],
            property_city=sanitized_data["property_city"],
            property_state=sanitized_data["property_state"],
            property_zip=sanitized_data["property_zip"],
            estimated_arv=sanitized_data["estimated_arv"],
            source=sanitized_data["source"],
            lead_status=sanitized_data["lead_status"],
            notes=sanitized_data["notes"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Lead created successfully with id: {db_lead.id}")
        return db_lead
        
    except ValueError as ve:
        logger.error(f"Lead validation error: {str(ve)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Failed to create lead: {str(e)}", exc_info=True)
        APIErrorLogger.log_api_error(
            endpoint="/leads",
            error=e,
            payload=lead.model_dump(exclude={"lead_email", "lead_phone"}),
            status_code=500
        )
        db.rollback()
        raise


def get_all_leads(db: Session, skip: int = 0, limit: int = 100) -> list[Lead]:
    """Retrieve all leads with pagination."""
    logger.debug(f"Fetching leads with skip={skip}, limit={limit}")
    return db.query(Lead).offset(skip).limit(limit).all()


def get_lead_by_id(db: Session, lead_id: int) -> Lead | None:
    """Get a specific lead by ID."""
    logger.debug(f"Fetching lead with id={lead_id}")
    return db.query(Lead).filter(Lead.id == lead_id).first()


def get_leads_by_status(db: Session, lead_status: str) -> list[Lead]:
    """Filter leads by status with sanitization."""
    # Sanitize status parameter
    sanitized_status = sanitize_input(lead_status)
    logger.debug(f"Fetching leads with status={sanitized_status}")
    
    valid_statuses = ["new", "contacted", "qualified", "working", "closed", "lost"]
    if sanitized_status not in valid_statuses:
        logger.warning(f"Invalid lead status requested: {sanitized_status}")
        return []
    
    return db.query(Lead).filter(Lead.lead_status == sanitized_status).all()


def update_lead_status(db: Session, lead_id: int, lead_status: str) -> Lead | None:
    """
    Update lead qualification status with validation.
    
    Args:
        db: Database session
        lead_id: Lead ID to update
        lead_status: New status value
    
    Returns:
        Updated Lead instance or None if not found
    """
    try:
        # Sanitize and validate status
        sanitized_status = sanitize_input(lead_status)
        valid_statuses = ["new", "contacted", "qualified", "working", "closed", "lost"]
        
        if sanitized_status not in valid_statuses:
            logger.warning(f"Attempted to set invalid status: {lead_status}")
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            logger.warning(f"Lead not found: id={lead_id}")
            return None
        
        old_status = db_lead.lead_status
        setattr(db_lead, "lead_status", sanitized_status)
        setattr(db_lead, "updated_at", datetime.utcnow())
        
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Lead {lead_id} status updated: {old_status} -> {sanitized_status}")
        return db_lead
        
    except ValueError as ve:
        logger.error(f"Status update validation error: {str(ve)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Failed to update lead status: {str(e)}", exc_info=True)
        db.rollback()
        raise


def delete_lead(db: Session, lead_id: int) -> bool:
    """Delete a lead."""
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not db_lead:
            logger.warning(f"Lead not found for deletion: id={lead_id}")
            return False
        
        db.delete(db_lead)
        db.commit()
        logger.info(f"Lead deleted: id={lead_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete lead {lead_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise
