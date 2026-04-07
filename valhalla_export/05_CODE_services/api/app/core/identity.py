"""
Centralized system identity configuration.

This module reads system email and from_name from environment variables
and provides a single source of truth for all outbound communications.

Environment Variables Required:
    VALHALLA_SYSTEM_EMAIL: The system's email address
    VALHALLA_FROM_NAME: The display name for system emails (defaults to "Valhalla Legacy Inc")
"""

import os
from typing import Dict, Any


def _get_system_email() -> str:
    """Get the system email from environment, raise if not set."""
    email = os.getenv("VALHALLA_SYSTEM_EMAIL")
    if not email:
        raise RuntimeError(
            "VALHALLA_SYSTEM_EMAIL is not set. "
            "Set this environment variable to configure the system email address."
        )
    return email


def _get_from_name() -> str:
    """Get the from name from environment, default to 'Valhalla Legacy Inc'."""
    return os.getenv("VALHALLA_FROM_NAME", "Valhalla Legacy Inc")


# Cache the identity at module load time to avoid repeated lookups
try:
    SYSTEM_EMAIL = _get_system_email()
    SYSTEM_FROM_NAME = _get_from_name()
except RuntimeError as e:
    # Allow graceful degradation if not in a context that requires email
    SYSTEM_EMAIL = None
    SYSTEM_FROM_NAME = None
    _INIT_ERROR = str(e)


def system_identity() -> Dict[str, str]:
    """
    Get the system identity.

    Returns:
        dict: A dictionary with keys:
            - email: The system's email address
            - from_name: The display name for system communications

    Raises:
        RuntimeError: If VALHALLA_SYSTEM_EMAIL is not configured.
    """
    if SYSTEM_EMAIL is None:
        raise RuntimeError(
            "VALHALLA_SYSTEM_EMAIL is not set. "
            "Set this environment variable to configure the system email address."
        )

    return {
        "email": SYSTEM_EMAIL,
        "from_name": SYSTEM_FROM_NAME,
    }


def get_system_email() -> str:
    """
    Get just the system email address.

    Returns:
        str: The system's email address.

    Raises:
        RuntimeError: If VALHALLA_SYSTEM_EMAIL is not configured.
    """
    identity = system_identity()
    return identity["email"]


def get_system_from_name() -> str:
    """
    Get just the from name.

    Returns:
        str: The display name for system communications.

    Raises:
        RuntimeError: If VALHALLA_SYSTEM_EMAIL is not configured.
    """
    identity = system_identity()
    return identity["from_name"]
