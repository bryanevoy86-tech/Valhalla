# Tunnel Setup Guide

## Option 1: Localtunnel (Free, No Signup) ⭐ RECOMMENDED

Localtunnel doesn't require authentication and is the fastest setup.

### Windows: Install Node.js first (if needed)
- Download from: https://nodejs.org/
- Then run:

```powershell
npx localtunnel --port 4000
```

You'll get output like:
```
your url is: https://abc123.loca.lt
```

Share that URL with WeWeb.

---

## Option 2: ngrok (Free Tier with Signup)

1. Sign up: https://dashboard.ngrok.com/signup
2. Get authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
3. Install: `pip install pyngrok`
4. Run:
```python
from pyngrok import ngrok
ngrok.set_auth_token("YOUR_AUTHTOKEN_HERE")
public_url = ngrok.connect(4000)
print(f"Tunnel: {public_url}")
```

---

## Option 3: Cloudflare Tunnel (Recommended for Production)

More stable than localtunnel, free tier available.

https://developers.cloudflare.com/cloudflare-one/connections/connect-applications/

---

## Once You Have the Public URL

Update WeWeb API connector to use:
```
https://your-tunnel-url/deals
```

Instead of:
```
http://localhost:4000/deals
```

Then all your API calls will work from WeWeb's hosted frontend.
