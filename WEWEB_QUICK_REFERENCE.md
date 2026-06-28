# WeWeb Auth - Quick Reference Card

## 📋 Copy-Paste Configuration

```bash
# Set these environment variables on your backend server
export VALHALLA_OWNER_USERNAME="owner@valhalla.local"
export VALHALLA_OWNER_PASSWORD="your-password-here"
export VALHALLA_JWT_SECRET="your-secret-key-here"
```

---

## 🔌 API Endpoints

```
POST   /api/weweb/login    → Get access token
GET    /api/weweb/me       → Get user info (needs token)
GET    /api/weweb/smoke    → Health check (public)
```

---

## 📝 Login Request

```bash
curl -X POST http://localhost:4000/api/weweb/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@valhalla.local","password":"password"}'
```

**Response:**
```json
{
  "ok": true,
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {"email": "owner@valhalla.local", "role": "owner"}
}
```

---

## 🔐 Authenticated Request

```bash
curl -X GET http://localhost:4000/api/weweb/me \
  -H "Authorization: Bearer eyJ..."
```

**Response:**
```json
{
  "ok": true,
  "user": {"email": "owner@valhalla.local", "role": "owner"}
}
```

---

## 🎯 For WeWeb Integration

1. **Login endpoint:** `POST /api/weweb/login`
2. **Extract token:** `response.access_token`
3. **Use in header:** `Authorization: Bearer <token>`
4. **Test endpoint:** `GET /api/weweb/me` with token
5. **Health check:** `GET /api/weweb/smoke` (no auth)

---

## ✅ Test Results

```
✅ 13 tests passing
✅ Login working
✅ Authentication working
✅ CORS configured
✅ Ready for production
```

---

## 🚫 Common Issues

| Issue | Solution |
|-------|----------|
| 401 on login | Check username/password matches `VALHALLA_OWNER_USERNAME` |
| 404 on endpoint | Ensure `VALHALLA_AUTH_ENABLED=true` before starting server |
| 401 on /me | Include `Authorization: Bearer <token>` header |
| CORS error | Already configured for all origins |

---

## 📂 Files Created

- ✅ `services/api/app/routers/weweb_auth.py` (220 lines)
- ✅ `tests/test_weweb_auth.py` (13 tests, all passing)
- ✅ Updated `services/api/app/main.py` (CORS headers)

---

**Everything is ready. Start your backend and test!**
