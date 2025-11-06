# Quick Start Guide - Why That Repo Works

## The Key Difference

The [ald0405/whoop-data](https://github.com/ald0405/whoop-data) repository works because it:
1. **Uses localhost** (`http://localhost:8765/callback`) - NOT a public HTTPS domain
2. **Has REAL Whoop credentials** from the Whoop Developer Portal
3. **Starts a local HTTP server** to receive the OAuth callback automatically

## Why Your App Wasn't Working

You were getting `request_forbidden` because:
- ❌ Using test/fake credentials (`76450e13-ba57-400e-a7a4-27494d51b842` is not a real Whoop Client ID)
- ❌ Trying to use `https://healthinsighttoday.com/callback` without a registered Whoop app

## ✅ Solution: Use Localhost (Like the Working Repo)

### Step 1: Get Real Whoop Credentials

You still need REAL credentials from Whoop:

1. Go to **https://developer.whoop.com/**
2. Sign in with your Whoop account
3. Create a new application:
   - **App Name**: HealthInsightToday (or any name)
   - **Redirect URI**: `http://localhost:8765/callback` ⬅️ Use localhost!
   - **Scopes**: Check all boxes

4. Copy your real Client ID and Client Secret

### Step 2: Update .env with REAL Credentials

```env
WHOOP_CLIENT_ID=your_real_client_id_here
WHOOP_CLIENT_SECRET=your_real_client_secret_here
```

**Note:** You do NOT need to set `WHOOP_REDIRECT_URI` - the script uses localhost by default!

### Step 3: Run the Localhost Version

```bash
python3 whoop_localhost.py
```

This will:
1. Start a local server on port 8765
2. Open your browser for Whoop authorization
3. Automatically receive the callback
4. Fetch all your Whoop data
5. Save to `whoop_data.json`

## 🔄 Localhost vs HTTPS Comparison

| Feature | Localhost (whoop_localhost.py) | HTTPS (whoop_auth.py) |
|---------|-------------------------------|----------------------|
| **Redirect URI** | `http://localhost:8765/callback` | `https://healthinsighttoday.com/callback` |
| **Setup Difficulty** | Easy - just run script | Requires web server/domain |
| **Use Case** | Development & Testing | Production deployment |
| **Callback** | Automatic (local server) | Manual (paste URL) |
| **Port Required** | 8765 must be free | N/A |
| **Works Locally** | ✅ Yes | ❌ No (needs live domain) |

## 📋 Quick Checklist

Before running `python3 whoop_localhost.py`:

- [ ] Have real WHOOP_CLIENT_ID from developer.whoop.com
- [ ] Have real WHOOP_CLIENT_SECRET from developer.whoop.com
- [ ] Added `http://localhost:8765/callback` as redirect URI in Whoop app
- [ ] Updated .env file with real credentials
- [ ] Port 8765 is available (not in use)

## 🎯 Which Script Should You Use?

### Use `whoop_localhost.py` if:
- ✅ You're developing/testing locally
- ✅ You want automatic callback handling
- ✅ You don't need a production deployment yet

### Use `whoop_auth.py` if:
- ✅ You have a live web server at healthinsighttoday.com
- ✅ You've deployed a /callback endpoint
- ✅ You need production-ready authentication

## 🚫 Common Mistake

❌ **Don't use fake/test credentials** - Whoop validates them!
```env
# These are NOT real credentials - they won't work!
WHOOP_CLIENT_ID=76450e13-ba57-400e-a7a4-27494d51b842
WHOOP_CLIENT_SECRET=9a24e6812963262f2a932907603626578592eadee2c28129a9313f8cd2d0
```

✅ **Get real credentials from https://developer.whoop.com/**

## 💡 TL;DR

The working repo uses:
1. **Localhost callback** (easy for development)
2. **Real Whoop credentials** (not fake ones)

To make yours work:
1. Get real credentials from Whoop Developer Portal
2. Use `http://localhost:8765/callback` as your redirect URI
3. Run `python3 whoop_localhost.py`

That's it! 🎉
