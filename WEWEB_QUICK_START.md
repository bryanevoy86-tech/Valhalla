# WeWeb Auth Bridge - Quick Start

## ⚡ 30-Second Setup

### For Local Dev Testing:
```bash
# 1. Set environment variables
export VALHALLA_OWNER_USERNAME="owner@valhalla.local"
export VALHALLA_OWNER_PASSWORD="dev-password-123"
export VALHALLA_JWT_SECRET="dev-secret-key"

# 2. Run the backend
python -m uvicorn app.main:app --port 4000

# 3. Run tests
pytest tests/test_weweb_auth.py -v
```

---

## 📝 Request Examples

### Test 1: Login
```bash
curl -X POST http://localhost:4000/api/weweb/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@valhalla.local","password":"dev-password-123"}'
```

**Response:**
```json
{
  "ok": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {"email": "owner@valhalla.local", "role": "owner"}
}
```

### Test 2: Get Current User
```bash
curl -X GET http://localhost:4000/api/weweb/me \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>"
```

### Test 3: Smoke Check
```bash
curl http://localhost:4000/api/weweb/smoke
```

---

## 🔌 WeWeb Integration

### In WeWeb:

1. **Login Action:**
   - Method: `POST /api/weweb/login`
   - Body: `{email, password}`
   - Store response: `data.access_token`

2. **Authenticated Requests:**
   - Add header: `Authorization: Bearer <token>`

3. **Example Flow:**
   ```javascript
   // Login
   const loginResponse = await fetch('/api/weweb/login', {
     method: 'POST',
     body: JSON.stringify({email: 'user@domain.com', password: 'pass'})
   });
   const {access_token} = await loginResponse.json();

   // Use token
   const meResponse = await fetch('/api/weweb/me', {
     headers: {'Authorization': `Bearer ${access_token}`}
   });
   ```

---

## 📍 Endpoint Reference

| Method | Endpoint | Auth | Response |
|--------|----------|------|----------|
| POST | `/api/weweb/login` | ❌ | `{ok, access_token, user}` |
| GET | `/api/weweb/me` | ✅ Bearer | `{ok, user}` |
| GET | `/api/weweb/smoke` | ❌ | `{ok, message}` |

---

## 🧪 Test Results

```
tests/test_weweb_auth.py ............. [100%]
13 passed in 6.43s
```

All tests passing:
- Login with valid credentials ✅
- Login with invalid credentials ✅  
- Get user info with token ✅
- Reject requests without token ✅
- CORS headers working ✅
- Complete login flow ✅

---

## ⚙️ Configuration

### Required Environment Variables:
```bash
VALHALLA_OWNER_USERNAME=owner@valhalla.local
VALHALLA_OWNER_PASSWORD=your-password
VALHALLA_JWT_SECRET=your-secret-key
```

### Token Expiry:
```bash
VALHALLA_TOKEN_TTL_SECONDS=3600  # 1 hour default
```

---

## 🚫 Known Limitations

- Single owner account (matching existing system)
- No role-based access control (admin only)
- Token must be refreshed after expiry

---

## 📂 Files Changed

```
✅ services/api/app/routers/weweb_auth.py (NEW - 220 lines)
✅ services/api/app/main.py (CORS header update)
✅ tests/test_weweb_auth.py (NEW - 190 lines, 13 tests)
```

---

## 🔒 Security Notes

- Passwords hashed with PBKDF2-SHA256
- JWT signed with secret key
- Bearer tokens expire after TTL
- CORS restricted to configured origins
- No hardcoded credentials in code

---

## ❓ Troubleshooting

**Q: Getting 401 on login?**
- Check credentials match `VALHALLA_OWNER_USERNAME` and password

**Q: Getting 404 on `/api/weweb/smoke`?**
- Ensure environment variables are set before starting server
- Check `VALHALLA_AUTH_ENABLED=true`

**Q: Token not working?**
- Token may have expired (default: 1 hour)
- Login again to get a fresh token
- Check header format: `Authorization: Bearer <token>`

---

## 📞 Support

All WeWeb endpoints are documented in OpenAPI:
```
http://localhost:4000/docs
```

Search for `weweb` tag to see all endpoints.
