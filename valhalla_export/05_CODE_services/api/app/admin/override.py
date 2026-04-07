"""Admin override - owner-only authorization."""
import hashlib


# In production, this should be securely stored/hashed
OWNER_PASSWORD_HASH = hashlib.sha256(b"HASHED_OWNER_PASSWORD").hexdigest()


def verify_owner_password(password: str) -> bool:
    """
    Verify owner password.
    
    Args:
        password: Owner password to verify
    
    Returns:
        bool - True if password matches
    """
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == OWNER_PASSWORD_HASH


def owner_override(password: str) -> dict:
    """
    Owner override for emergency access.
    
    Args:
        password: Owner password
    
    Returns:
        dict with override result
    """
    if verify_owner_password(password):
        return {
            "status": "authorized",
            "owner": True,
            "message": "Owner authorization confirmed"
        }
    
    return {
        "status": "unauthorized",
        "owner": False,
        "message": "Invalid owner password"
    }


def emergency_shutdown(password: str):
    """Emergency shutdown with owner authentication."""
    if not verify_owner_password(password):
        return {
            "status": "unauthorized",
            "message": "Invalid owner password"
        }
    
    # Return to sandbox
    from app.admin.runtime import return_to_sandbox
    return_to_sandbox()
    
    return {
        "status": "emergency_shutdown",
        "message": "System shut down and returned to SANDBOX"
    }
