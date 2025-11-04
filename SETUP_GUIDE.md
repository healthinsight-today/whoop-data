# Setting Up Whoop API Integration

## 🔑 Getting Real Credentials

You need to register your app with Whoop to get valid credentials. Here's how:

### Step 1: Create a Whoop Developer Account

1. Go to **https://developer.whoop.com/**
2. Sign in with your Whoop account
3. Navigate to the **Developer Portal** or **API Console**

### Step 2: Create a New Application

1. Click **"Create Application"** or **"New App"**
2. Fill in the application details:
   - **App Name**: HealthInsightToday (or your preferred name)
   - **Description**: Health data integration for HealthInsightToday.com
   - **Redirect URI**: `https://healthinsighttoday.com/callback`
   - **Scopes**: Select all the data you need:
     - ✓ `read:profile`
     - ✓ `read:body_measurement`
     - ✓ `read:recovery`
     - ✓ `read:sleep`
     - ✓ `read:workout`
     - ✓ `read:cycles`

3. **Save** the application

### Step 3: Get Your Credentials

After creating the app, you'll receive:
- **Client ID** (looks like: `YOUR_CLIENT_ID_HERE`)
- **Client Secret** (looks like: `YOUR_CLIENT_SECRET_HERE`)

⚠️ **Important**: Keep your Client Secret private! Don't share it publicly.

### Step 4: Update Your .env File

Open your `.env` file and update it with your **real credentials**:

```env
# Whoop API Credentials
WHOOP_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID_FROM_WHOOP
WHOOP_CLIENT_SECRET=YOUR_ACTUAL_CLIENT_SECRET_FROM_WHOOP
WHOOP_REDIRECT_URI=https://healthinsighttoday.com/callback
```

### Step 5: Verify Redirect URI

Make sure the **exact redirect URI** is registered in your Whoop app:
- In Whoop Developer Portal: `https://healthinsighttoday.com/callback`
- In your .env file: `https://healthinsighttoday.com/callback`

They must match **exactly** (including https:// and no trailing slash).

## 🚀 Running the Script

After updating with real credentials:

```bash
python3 whoop_auth.py
```

## 🔍 Troubleshooting

### Error: `request_forbidden`
- **Cause**: Invalid credentials or app not configured
- **Fix**: Use real credentials from Whoop Developer Portal

### Error: `invalid_redirect_uri`
- **Cause**: Redirect URI doesn't match
- **Fix**: Make sure the redirect URI in your app settings matches exactly

### Error: `invalid_state`
- **Cause**: State parameter issue (already fixed in our script)
- **Fix**: Already handled by the script

### Error: `invalid_scope`
- **Cause**: Requesting scopes not approved for your app
- **Fix**: Make sure all scopes are enabled in your Whoop app settings

## 📋 Checklist

Before running the script, verify:

- [ ] Created app in Whoop Developer Portal
- [ ] Got real Client ID and Client Secret
- [ ] Added `https://healthinsighttoday.com/callback` as redirect URI in Whoop app
- [ ] Updated `.env` file with real credentials
- [ ] All required scopes are enabled in Whoop app settings

## 🔗 Useful Links

- Whoop Developer Portal: https://developer.whoop.com/
- Whoop API Documentation: https://developer.whoop.com/api
- OAuth 2.0 Flow: https://developer.whoop.com/docs/developing/oauth

## 💡 Alternative: Test with Localhost

If you want to test locally first, you can:

1. Add `http://localhost:8080/callback` to your Whoop app's redirect URIs
2. Update `.env`: `WHOOP_REDIRECT_URI=http://localhost:8080/callback`
3. Run `python3 whoop_simple.py` (uses local server)

This way you can test locally before deploying to production.

## 📞 Need Help?

If you're still having issues:
1. Double-check credentials are correct (copy-paste from Whoop portal)
2. Verify redirect URI matches exactly
3. Make sure your Whoop app is in "Active" status
4. Check if you need to request production access (some APIs require approval)
