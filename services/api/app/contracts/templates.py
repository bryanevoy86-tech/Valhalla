"""
Module 59: DocuSign Template Loader
Load and manage DocuSign contract templates.
"""
from typing import Dict, Any, Optional


def load_template(template_code: str) -> Dict[str, Any]:
    """
    Load a DocuSign contract template.
    
    Args:
        template_code: Template identifier (e.g., 'OFFER', 'CONTRACT')
    
    Returns:
        dict: Template data
    """
    templates = {
        "OFFER": {
            "code": "OFFER",
            "name": "Real Estate Offer",
            "fields": ["price", "earnest_money", "contingencies"],
            "status": "active"
        },
        "CONTRACT": {
            "code": "CONTRACT",
            "name": "Real Estate Purchase Agreement",
            "fields": ["price", "closing_date", "parties"],
            "status": "active"
        },
        "DISCLOSURE": {
            "code": "DISCLOSURE",
            "name": "Property Disclosure",
            "fields": ["property_address", "issues"],
            "status": "active"
        }
    }
    
    if template_code in templates:
        return {
            "status": "loaded",
            "template": templates[template_code]
        }
    
    return {
        "status": "not_found",
        "message": f"Template {template_code} not found"
    }


def list_templates() -> Dict[str, Any]:
    """
    List all available templates.
    
    Returns:
        dict: List of templates
    """
    return {
        "status": "retrieved",
        "templates": [
            {"code": "OFFER", "name": "Real Estate Offer"},
            {"code": "CONTRACT", "name": "Real Estate Purchase Agreement"},
            {"code": "DISCLOSURE", "name": "Property Disclosure"}
        ]
    }


def get_template_fields(template_code: str) -> Dict[str, Any]:
    """
    Get required fields for a template.
    
    Args:
        template_code: Template identifier
    
    Returns:
        dict: Template fields
    """
    template = load_template(template_code)
    
    if template.get("status") == "loaded":
        return {
            "status": "retrieved",
            "template_code": template_code,
            "fields": template["template"].get("fields", [])
        }
    
    return {
        "status": "error",
        "message": f"Template {template_code} not found"
    }
