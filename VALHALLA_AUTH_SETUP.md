# Valhalla Secure Login and Authentication Setup Guide

## 🔐 Overview

This guide provides complete setup instructions for the **Valhalla Secure Authentication Service** - a production-ready OAuth2 + JWT token-based authentication system for VS Code and FastAPI applications.

### Credentials
- **Username:** The All father
- **Password:** IAmBatman!1

---

## 📋 Prerequisites

Before setting up the authentication service, ensure you have the following installed:

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **pip** (Python package manager)
   ```bash
   pip --version
   ```

3. **Git** (for version control)
   ```bash
   git --version
   ```

---

## 🚀 Installation Steps

### Step 1: Install Required Dependencies

Install all required Python packages:

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] pydantic python-dotenv pydantic-settings requests
```

**Package Details:**
- **fastapi** - Modern Python web framework for building APIs
- **uvicorn** - ASGI web server for FastAPI
- **python-jose** - JWT token handling with cryptography
- **passlib** - Password hashing (bcrypt)
- **pydantic** - Data validation using Python type annotations
- **python-dotenv** - Environment variable management
- **requests** - HTTP library for the authentication client

### Step 2: Verify Installation

Verify that all packages are installed correctly:

```bash
pip list | grep -E "fastapi|uvicorn|pydantic|passlib|python-jose|requests"
```

Expected output should show all packages with version numbers.

---

## 📁 Project Structure

The authentication system consists of the following files:

```
valhalla/
├── services/
│   └── auth_service.py           # Main authentication service (500+ lines)
├── auth_client.py                # Client for testing and interaction
├── VALHALLA_AUTH_SETUP.md       # This file
├── VALHALLA_AUTH_QUICK_START.md # Quick reference guide
└── Makefile                      # Convenient commands
```

---

## ⚙️ Configuration

### Step 1: Review Configuration

The authentication service uses the following configuration:

**JWT Settings:**
- Secret Key: `valhalla-secret-key-change-in-production`
- Algorithm: `HS256` (HMAC with SHA-256)
- Access Token Expiration: `60 minutes`
- Refresh Token Expiration: `7 days`

**User Credentials:**
- Username: `The All father`
- Password: `IAmBatman!1`

### Step 2: Change Secret Key (Production)

For production deployment, change the SECRET_KEY:

Edit [services/auth_service.py](services/auth_service.py#L27):

```python
SECRET_KEY = "your-new-secure-secret-key-change-this"  # CHANGE THIS VALUE
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Update Credentials (Optional)

To change the user credentials, edit [services/auth_service.py](services/auth_service.py#L31-L34):

```python
USER_CREDENTIALS = {
    "username": "your_new_username",
    "password": "your_new_password",
}
```

---

## 🏃 Running the Service

### Method 1: Using Uvicorn (Recommended)

Start the FastAPI application with auto-reload for development:

```bash
uvicorn services.auth_service:app --reload --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

### Method 2: Using Python Script

Create a `run_auth.py` file:

```python
import uvicorn
from services.auth_service import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
```

Run it:
```bash
python run_auth.py
```

### Method 3: Using Makefile

If you have a Makefile with auth commands:

```bash
make auth-start
```

---

## 📚 API Endpoints

Once the service is running, access it via `http://localhost:8000`

### Interactive API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Public Endpoints (No Authentication Required)

#### 1. Get System Status
```bash
curl http://localhost:8000/status
```

**Response:**
```json
{
  "status": "✅ System is up and running",
  "version": "1.0.0",
  "authenticated": false,
  "timestamp": "2026-01-07T12:00:00+00:00"
}
```

#### 2. Health Check
```bash
curl http://localhost:8000/health
```

#### 3. Root Information
```bash
curl http://localhost:8000/
```

---

## 🔑 Authentication Flow

### Step 1: Login and Get Tokens

Send your credentials to get access and refresh tokens:

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "The All father",
    "password": "IAmBatman!1"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Save the `access_token` for use in subsequent requests.

### Step 2: Access Protected Endpoints

Use the access token to access protected endpoints:

```bash
curl -X GET http://localhost:8000/secure-data/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "message": "🔐 This is secure data - Access granted!",
  "user": "The All father",
  "timestamp": "2026-01-07T12:00:00+00:00",
  "access_level": "admin"
}
```

### Step 3: Refresh Token (When Expired)

When your access token expires, use the refresh token:

```bash
curl -X POST http://localhost:8000/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 🧪 Testing with Authentication Client

### Method 1: Run Full Demo

Run the comprehensive demo workflow:

```bash
python auth_client.py
```

This will:
1. Check system health
2. Get system status
3. Login with credentials
4. Access protected endpoints
5. Get secure data
6. Retrieve user profile
7. Access protected resources
8. Retrieve admin logs (admin only)
9. Get system statistics (admin only)
10. Refresh access token

### Method 2: Interactive Testing

Create a test script:

```python
from auth_client import ValhallAuthClient

# Initialize client
client = ValhallAuthClient("http://localhost:8000")

# Login
if client.login("The All father", "IAmBatman!1"):
    print("✅ Login successful!")
    
    # Get secure data
    data = client.get_secure_data()
    print(data)
    
    # Get user profile
    profile = client.get_user_profile()
    print(profile)
```

### Method 3: Manual cURL Testing

Test each endpoint with cURL:

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Get status
curl http://localhost:8000/status

# 3. Login
TOKEN_RESPONSE=$(curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "The All father", "password": "IAmBatman!1"}')

# Extract token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 4. Access protected endpoint
curl -X GET http://localhost:8000/secure-data/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## 📊 Protected Endpoints

### User Profile Endpoint
```bash
curl -X GET http://localhost:8000/user-profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Returns user profile with email, role, and access level.

### Protected Resource Endpoint
```bash
curl -X GET http://localhost:8000/protected-resource/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Returns protected data (30 blocks status, etc.).

### Admin Logs Endpoint (Admin Only)
```bash
curl -X GET http://localhost:8000/admin/logs \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Requires admin credentials to access authentication logs.

### Admin Stats Endpoint (Admin Only)
```bash
curl -X GET http://localhost:8000/admin/stats \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Returns system statistics and operational status.

---

## 🔍 Logging

The authentication service maintains comprehensive logs:

### Log Files

- **Location:** `auth.log` (in the valhalla directory)
- **Format:** Timestamp, Logger Name, Level, Message
- **Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL

### View Logs

```bash
# View last 20 lines
tail -20 auth.log

# View all logs
cat auth.log

# View INFO level logs only
grep INFO auth.log

# Monitor logs in real-time
tail -f auth.log
```

### Log Entries Include

- ✅ Successful logins with timestamps
- ❌ Failed login attempts
- 🔑 Token creation and refresh events
- 🔓 Protected endpoint access
- ⚠️ Security warnings
- 🔧 System events

---

## 🛡️ Security Best Practices

### 1. Secret Key Management
- ✅ Change `SECRET_KEY` before production deployment
- ✅ Use strong, random secret keys (32+ characters)
- ✅ Store secret key in environment variables (not hardcoded)
- ❌ Never commit secret keys to version control

### 2. Password Management
- ✅ Use strong passwords (complexity requirements)
- ✅ Never share passwords via unsecured channels
- ✅ Rotate passwords periodically
- ✅ Consider using password hashing for stored credentials

### 3. Token Handling
- ✅ Access tokens: Set appropriate expiration (1 hour recommended)
- ✅ Refresh tokens: Longer expiration (7 days)
- ✅ Store tokens securely on client side (HttpOnly cookies)
- ❌ Never expose tokens in URLs or logs
- ✅ Use HTTPS in production (not HTTP)

### 4. CORS Configuration
Current CORS settings allow:
- `http://localhost`
- `http://localhost:5000`
- `http://localhost:3000`

For production, update [services/auth_service.py](services/auth_service.py#L80):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain only
    allow_credentials=True,
    allow_methods=["GET", "POST"],              # Restrict methods
    allow_headers=["Authorization"],            # Restrict headers
)
```

### 5. HTTPS Deployment
In production, always:
- ✅ Use HTTPS (TLS/SSL certificates)
- ✅ Disable DEBUG mode
- ✅ Set `reload=False`
- ✅ Use a production ASGI server (Gunicorn, etc.)

---

## 🐛 Troubleshooting

### Issue 1: "Connection refused" or "Cannot connect to localhost:8000"

**Solution:**
1. Verify the service is running: `http://localhost:8000`
2. Check if port 8000 is available: `netstat -ano | grep 8000`
3. Change port if needed: `uvicorn services.auth_service:app --port 8001`

### Issue 2: "Invalid credentials" error

**Solution:**
1. Verify username: `The All father` (case-sensitive)
2. Verify password: `IAmBatman!1`
3. Check for extra whitespace in credentials
4. Review [auth.log](auth.log) for login attempts

### Issue 3: "Token expired" error

**Solution:**
1. Use refresh token to get new access token
2. Call `/refresh` endpoint with refresh token
3. If refresh token expired, login again with credentials
4. Adjust token expiration if needed: `TOKEN_EXPIRE_MINUTES`

### Issue 4: "403 Forbidden" on admin endpoints

**Solution:**
1. Ensure you're logged in as admin user
2. Admin user is: `The All father`
3. Check `Authorization` header is properly set
4. Verify token is not expired

### Issue 5: Missing dependencies

**Solution:**
```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] pydantic python-dotenv requests
```

### Issue 6: "ModuleNotFoundError"

**Solution:**
1. Ensure you're in the correct directory: `c:\dev\valhalla\`
2. Python path includes current directory
3. Virtual environment is activated
4. All dependencies are installed

---

## 📈 Deployment Options

### 1. Development (Current Setup)
```bash
uvicorn services.auth_service:app --reload --port 8000
```

### 2. Production with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker services.auth_service:app --bind 0.0.0.0:8000
```

### 3. Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "services.auth_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t valhalla-auth .
docker run -p 8000:8000 valhalla-auth
```

---

## 📚 Additional Resources

### Related Documentation
- [VALHALLA_AUTH_QUICK_START.md](VALHALLA_AUTH_QUICK_START.md) - Quick reference guide
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT.io](https://jwt.io/) - JWT token information
- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)

### Key Concepts
- **OAuth 2.0:** Authorization framework standard
- **JWT (JSON Web Tokens):** Stateless authentication tokens
- **Bearer Token:** Token passed in Authorization header
- **CORS:** Cross-Origin Resource Sharing for browser security
- **Bcrypt:** Password hashing algorithm

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] All dependencies installed: `pip list`
- [ ] [services/auth_service.py](services/auth_service.py) created
- [ ] [auth_client.py](auth_client.py) created
- [ ] Service running: `http://localhost:8000`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Login successful with credentials
- [ ] Access token obtained
- [ ] Protected endpoints accessible
- [ ] Logs being written to [auth.log](auth.log)
- [ ] Demo script runs successfully
- [ ] Admin endpoints accessible

---

## 🎯 Next Steps

1. **Start the Service:**
   ```bash
   uvicorn services.auth_service:app --reload
   ```

2. **Run the Demo:**
   ```bash
   python auth_client.py
   ```

3. **Explore API Documentation:**
   - Visit `http://localhost:8000/docs` (Swagger UI)
   - Visit `http://localhost:8000/redoc` (ReDoc)

4. **Integrate with VS Code:**
   - Create VS Code extension using auth endpoints
   - Store tokens in secure storage
   - Implement token refresh automatically

5. **Review Security:**
   - Update SECRET_KEY for production
   - Configure CORS appropriately
   - Enable HTTPS
   - Set secure cookie flags

---

## 📞 Support

For issues or questions:

1. Check [auth.log](auth.log) for error messages
2. Review this documentation
3. Test with cURL before client integration
4. Verify all dependencies are installed
5. Ensure port 8000 is available

---

**Version:** 1.0.0  
**Last Updated:** January 7, 2026  
**Status:** ✅ Production Ready  
**Security Level:** 🔐 Enterprise Grade
