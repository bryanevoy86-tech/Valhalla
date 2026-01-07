"""
Valhalla Secure Authentication Module
OAuth2 + JWT Token-based Authentication
Protected Routes with Role-based Access Control
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import jwt
from datetime import datetime, timedelta, timezone
import logging
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VSCode_Auth")

# ============================================================================
# CONFIGURATION
# ============================================================================

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "valhalla-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# User Credentials (Replace with your desired username and password)
USER_CREDENTIALS = {
    "username": "The All father",
    "password": "IAmBatman!1",
}

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class User(BaseModel):
    """User model for login"""
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")


class Token(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    exp: Optional[datetime] = None


class SecureData(BaseModel):
    """Secure data response model"""
    message: str
    user: str
    timestamp: str
    access_level: str


class SystemStatus(BaseModel):
    """System status response model"""
    status: str
    version: str
    authenticated: bool
    timestamp: str


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Access token created for user: {data.get('sub')}")
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Refresh token created for user: {data.get('sub')}")
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
        return token_data
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Get current authenticated user from token"""
    token_data = verify_token(token)
    return token_data.username


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Valhalla Authentication Service",
    description="Secure OAuth2 + JWT Authentication for Valhalla VS Code",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/token", response_model=Token, tags=["Authentication"])
def login_for_access_token(form_data: User) -> Token:
    """
    Login endpoint to authenticate user and receive JWT tokens.
    
    **Returns:**
    - access_token: JWT access token (valid for 1 hour)
    - refresh_token: JWT refresh token (valid for 7 days)
    - token_type: Always "bearer"
    - expires_in: Token expiration time in seconds
    """
    # Verify credentials
    if form_data.username != USER_CREDENTIALS["username"]:
        logger.warning(f"Login attempt with invalid username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if form_data.password != USER_CREDENTIALS["password"]:
        logger.warning(f"Login attempt with invalid password for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": form_data.username})
    
    logger.info(f"✅ Successful login for user: {form_data.username}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/refresh", response_model=Token, tags=["Authentication"])
def refresh_access_token(token: str = Depends(oauth2_scheme)) -> Token:
    """
    Refresh endpoint to get a new access token using a refresh token.
    
    **Returns:**
    - access_token: New JWT access token
    - token_type: Always "bearer"
    - expires_in: Token expiration time in seconds
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        
        logger.info(f"✅ Access token refreshed for user: {username}")
        
        return Token(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


# ============================================================================
# PROTECTED ENDPOINTS
# ============================================================================

@app.get("/secure-data/", response_model=SecureData, tags=["Protected"])
def read_secure_data(current_user: str = Depends(get_current_user)) -> SecureData:
    """
    Protected endpoint that requires valid authentication token.
    
    **Returns:**
    - message: Secure data message
    - user: Authenticated username
    - timestamp: Current timestamp
    - access_level: User access level
    """
    logger.info(f"✅ Secure data accessed by user: {current_user}")
    
    return SecureData(
        message="🔐 This is secure data - Access granted!",
        user=current_user,
        timestamp=datetime.now(timezone.utc).isoformat(),
        access_level="admin"
    )


@app.get("/user-profile/", tags=["Protected"])
def get_user_profile(current_user: str = Depends(get_current_user)):
    """
    Get user profile information (protected endpoint).
    """
    logger.info(f"✅ User profile accessed by: {current_user}")
    
    return {
        "username": current_user,
        "email": f"{current_user.lower().replace(' ', '.')}@valhalla.local",
        "role": "administrator",
        "access_level": "full",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat()
    }


@app.get("/protected-resource/", tags=["Protected"])
def access_protected_resource(current_user: str = Depends(get_current_user)):
    """
    Access a protected resource (requires valid token).
    """
    logger.info(f"✅ Protected resource accessed by: {current_user}")
    
    return {
        "resource": "Protected Data",
        "data": [
            {"id": 1, "name": "Block 1", "status": "active"},
            {"id": 2, "name": "Block 2", "status": "active"},
            {"id": 3, "name": "Block 3", "status": "active"},
        ],
        "user": current_user,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# LOGGING & MONITORING ENDPOINTS
# ============================================================================

@app.get("/log-test", tags=["Logging"])
def log_test():
    """
    Test logging endpoint to verify logging functionality.
    """
    logger.info("✅ Test log entry created")
    logger.debug("Debug message")
    logger.warning("Warning message")
    
    return {
        "message": "✅ Log created successfully",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "log_file": "auth.log"
    }


@app.get("/status", response_model=SystemStatus, tags=["Monitoring"])
def system_status():
    """
    Get current system status.
    """
    logger.info("✅ System status checked")
    
    return SystemStatus(
        status="✅ System is up and running",
        version="1.0.0",
        authenticated=False,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@app.get("/health", tags=["Monitoring"])
def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/admin/logs", tags=["Admin"])
def get_logs(current_user: str = Depends(get_current_user)):
    """
    Admin endpoint to view authentication logs.
    """
    if current_user != USER_CREDENTIALS["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    logger.info(f"✅ Logs accessed by admin: {current_user}")
    
    try:
        with open('auth.log', 'r') as f:
            logs = f.readlines()[-50:]  # Last 50 lines
        return {
            "user": current_user,
            "total_lines": len(logs),
            "logs": logs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except FileNotFoundError:
        return {
            "user": current_user,
            "message": "No logs file found yet",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.get("/admin/stats", tags=["Admin"])
def admin_stats(current_user: str = Depends(get_current_user)):
    """
    Admin endpoint to view authentication statistics.
    """
    if current_user != USER_CREDENTIALS["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    logger.info(f"✅ Stats accessed by admin: {current_user}")
    
    return {
        "admin": current_user,
        "total_blocks": 30,
        "active_blocks": 30,
        "system_status": "operational",
        "authentication_method": "OAuth2 + JWT",
        "uptime": "continuous",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "Valhalla Authentication Service",
        "version": "1.0.0",
        "description": "Secure OAuth2 + JWT Authentication",
        "user": "The All father",
        "endpoints": {
            "login": "/token",
            "refresh": "/refresh",
            "secure_data": "/secure-data/",
            "user_profile": "/user-profile/",
            "protected_resource": "/protected-resource/",
            "status": "/status",
            "health": "/health",
            "logs": "/log-test",
            "admin_logs": "/admin/logs",
            "admin_stats": "/admin/stats"
        },
        "documentation": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    logger.info("🚀 Valhalla Authentication Service initialized")
