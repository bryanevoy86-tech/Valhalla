# 🔐 Valhalla Authentication - Quick Start Guide

**TL;DR** - Get the secure authentication system running in 5 minutes.

---

## ⚡ Quick Setup (5 Minutes)

### 1. Install Dependencies (1 minute)
```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] pydantic python-dotenv requests
```

### 2. Start the Service (1 minute)
```bash
cd c:\dev\valhalla
uvicorn services.auth_service:app --reload
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 3. Test in Another Terminal (1 minute)
```bash
python auth_client.py
```

### 4. Access Dashboard (1 minute)
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 5. Done! ✅
Your secure authentication service is running.

---

## 🔑 Login Credentials

| Field | Value |
|-------|-------|
| **Username** | The All father |
| **Password** | IAmBatman!1 |

---

## 📋 Core Endpoints

### Authentication
```bash
# Login and get tokens
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "The All father", "password": "IAmBatman!1"}'

# Response:
# {
#   "access_token": "eyJhbGc...",
#   "refresh_token": "eyJhbGc...",
#   "token_type": "bearer",
#   "expires_in": 3600
# }
```

### Protected Data (Requires Token)
```bash
curl -X GET http://localhost:8000/secure-data/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

### Public Endpoints (No Token Needed)
```bash
# System Status
curl http://localhost:8000/status

# Health Check
curl http://localhost:8000/health

# Root Info
curl http://localhost:8000/
```

---

## 🧪 Full Endpoint List

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/token` | POST | ❌ No | Login and get tokens |
| `/refresh` | POST | ✅ Yes | Refresh access token |
| `/secure-data/` | GET | ✅ Yes | Protected data access |
| `/user-profile/` | GET | ✅ Yes | Get user profile |
| `/protected-resource/` | GET | ✅ Yes | Access protected resource |
| `/status` | GET | ❌ No | System status |
| `/health` | GET | ❌ No | Health check |
| `/log-test` | GET | ❌ No | Test logging |
| `/admin/logs` | GET | ✅ Yes | Admin: View logs |
| `/admin/stats` | GET | ✅ Yes | Admin: View statistics |
| `/` | GET | ❌ No | API information |

---

## 🔄 Authentication Flow Diagram

```
┌─────────────────────────────────────────────────┐
│ 1. Send Credentials to /token                   │
│    {username, password}                         │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│ 2. Receive Tokens & Token Type                  │
│    access_token, refresh_token, expires_in      │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│ 3. Use Access Token for Protected Endpoints     │
│    Authorization: Bearer {access_token}         │
└──────────────────┬──────────────────────────────┘
                   ↓
         ┌─────────┴──────────┐
         ↓                    ↓
    ✅ Success          ❌ Token Expired
         │                    │
         ↓                    ↓
    Access Data         Call /refresh with
    Continue            refresh_token
                             │
                             ↓
                        New access_token
                             │
                             ↓
                        Use for Protected
                        Endpoints
```

---

## 💡 Common Usage Examples

### Example 1: Login and Access Protected Data
```bash
#!/bin/bash

# 1. Login
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "The All father", "password": "IAmBatman!1"}')

# 2. Extract access token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 3. Access protected endpoint
curl -X GET http://localhost:8000/secure-data/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. Output: Secure data!
```

### Example 2: Get User Profile
```bash
curl -X GET http://localhost:8000/user-profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Output:
# {
#   "username": "The All father",
#   "email": "the.all.father@valhalla.local",
#   "role": "administrator",
#   "access_level": "full",
#   "created_at": "...",
#   "last_login": "..."
# }
```

### Example 3: View System Statistics (Admin)
```bash
curl -X GET http://localhost:8000/admin/stats \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Output:
# {
#   "admin": "The All father",
#   "total_blocks": 30,
#   "active_blocks": 30,
#   "system_status": "operational",
#   "authentication_method": "OAuth2 + JWT",
#   "uptime": "continuous"
# }
```

---

## 🧯 Troubleshooting

### Q: Service won't start
**A:** Ensure port 8000 is available. Try: `uvicorn services.auth_service:app --port 8001`

### Q: Login fails with "Invalid credentials"
**A:** Use exact credentials:
- Username: `The All father` (case-sensitive)
- Password: `IAmBatman!1`

### Q: "Token expired" error
**A:** Use refresh token or login again

### Q: Can't access protected endpoints
**A:** Ensure Authorization header includes: `Bearer {access_token}`

### Q: Port already in use
**A:** Change port: `uvicorn services.auth_service:app --port 8001`

### Q: Module not found error
**A:** Run: `pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] pydantic python-dotenv requests`

---

## 📊 Token Information

### Access Token
- **Expiration:** 60 minutes (configurable)
- **Type:** JWT (JSON Web Token)
- **Algorithm:** HS256
- **Usage:** All protected endpoints
- **Format:** `Authorization: Bearer {token}`

### Refresh Token
- **Expiration:** 7 days (configurable)
- **Type:** JWT (JSON Web Token)
- **Usage:** Get new access token when expired
- **Endpoint:** `/refresh`

---

## 🎯 What's Included

✅ **Authentication Service** - [services/auth_service.py](services/auth_service.py)
- OAuth2 + JWT implementation
- 10+ protected and public endpoints
- Comprehensive logging
- Admin endpoints for monitoring
- User profile management

✅ **Client Library** - [auth_client.py](auth_client.py)
- Easy-to-use authentication client
- Automatic token management
- Demo workflow
- Error handling

✅ **Documentation** - Multiple guides
- Full setup guide: [VALHALLA_AUTH_SETUP.md](VALHALLA_AUTH_SETUP.md)
- This quick start: [VALHALLA_AUTH_QUICK_START.md](VALHALLA_AUTH_QUICK_START.md)

---

## 🔐 Security Features

✅ **JWT Tokens** - Stateless authentication  
✅ **Token Expiration** - Time-limited access  
✅ **Refresh Tokens** - Extended session support  
✅ **Password Security** - Bcrypt hashing ready  
✅ **CORS Protection** - Controlled cross-origin access  
✅ **Logging** - Complete audit trail  
✅ **Role-based Access** - Admin-only endpoints  
✅ **HTTP/HTTPS Ready** - Production deployment support

---

## 📞 File Locations

| File | Purpose |
|------|---------|
| [services/auth_service.py](services/auth_service.py) | Main authentication service |
| [auth_client.py](auth_client.py) | Python client for testing |
| [VALHALLA_AUTH_SETUP.md](VALHALLA_AUTH_SETUP.md) | Comprehensive setup guide |
| [VALHALLA_AUTH_QUICK_START.md](VALHALLA_AUTH_QUICK_START.md) | This quick start |
| [auth.log](auth.log) | Authentication logs |

---

## 🚀 Next Steps

1. **Start service:** `uvicorn services.auth_service:app --reload`
2. **Run demo:** `python auth_client.py`
3. **Explore API:** http://localhost:8000/docs
4. **Review logs:** `tail -f auth.log`
5. **Integrate with your app:** Use `auth_client.py` as reference

---

## ✨ You're Ready!

Your secure authentication system is ready to use. Visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

🎉 **Authentication is live and secure!**

---

**Version:** 1.0.0 | **Status:** ✅ Ready | **Last Updated:** January 7, 2026
