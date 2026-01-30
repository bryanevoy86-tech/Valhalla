"""
Email Identity Guard

Prevents VAs and other actors from using unauthorized email addresses.
Ensures all outbound emails come from the configured system email only.
"""

from app.core.identity import get_system_email


class UnauthorizedEmailError(PermissionError):
    """Raised when an unauthorized email identity is used."""

    pass


def assert_system_email(email: str) -> None:
    """
    Assert that the provided email matches the system email.

    Used as a guardrail to prevent personal or rogue email usage.

    Args:
        email: The email address to validate

    Raises:
        UnauthorizedEmailError: If the email doesn't match the system email

    Example:
        >>> assert_system_email("system@example.com")  # OK
        >>> assert_system_email("personal@example.com")  # Raises UnauthorizedEmailError
    """
    system_email = get_system_email()

    if email != system_email:
        raise UnauthorizedEmailError(
            f"Unauthorized email identity: {email}. "
            f"Only {system_email} is allowed."
        )


def validate_sender_email(sender_email: str) -> bool:
    """
    Validate that a sender email is authorized.

    Args:
        sender_email: The email address to validate

    Returns:
        bool: True if authorized, False otherwise
    """
    try:
        assert_system_email(sender_email)
        return True
    except UnauthorizedEmailError:
        return False


def get_authorized_emails() -> list[str]:
    """
    Get the list of authorized email addresses for system communications.

    Currently only the system email is authorized.

    Returns:
        list[str]: List containing the authorized system email
    """
    return [get_system_email()]
