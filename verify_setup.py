#!/usr/bin/env python3
"""
Verify your Whoop API setup before running the main script
"""

import os
from dotenv import load_dotenv

load_dotenv()

def verify_setup():
    """Verify that all credentials and settings are configured"""

    print("=" * 70)
    print(" " * 15 + "WHOOP API SETUP VERIFICATION")
    print("=" * 70)
    print()

    issues = []
    warnings = []

    # Check Client ID
    client_id = os.getenv("WHOOP_CLIENT_ID")
    if not client_id:
        issues.append("❌ WHOOP_CLIENT_ID is not set in .env file")
    elif client_id == "76450e13-ba57-400e-a7a4-27494d51b842":
        issues.append("❌ WHOOP_CLIENT_ID appears to be a placeholder/test value")
        print("   You need to get real credentials from https://developer.whoop.com/")
    else:
        print(f"✓ Client ID: {client_id[:20]}... (looks valid)")

    # Check Client Secret
    client_secret = os.getenv("WHOOP_CLIENT_SECRET")
    if not client_secret:
        issues.append("❌ WHOOP_CLIENT_SECRET is not set in .env file")
    elif client_secret == "9a24e6812963262f2a932907603626578592eadee2c28129a9313f8cd2d0":
        issues.append("❌ WHOOP_CLIENT_SECRET appears to be a placeholder/test value")
        print("   You need to get real credentials from https://developer.whoop.com/")
    else:
        print(f"✓ Client Secret: {client_secret[:20]}... (looks valid)")

    # Check Redirect URI
    redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8080/callback")
    print(f"✓ Redirect URI: {redirect_uri}")

    if redirect_uri == "http://localhost:8080/callback":
        warnings.append("⚠ Using localhost redirect URI - good for testing")
        print("   For production, use: https://healthinsighttoday.com/callback")
    elif redirect_uri.startswith("http://"):
        warnings.append("⚠ Using HTTP (not HTTPS) - Whoop may reject this in production")
    else:
        print("   Make sure this EXACT URL is registered in your Whoop app settings!")

    # Check for token file
    if os.path.exists(".whoop_tokens.json"):
        print("✓ Token file exists (.whoop_tokens.json)")
        print("   If you're having auth issues, try deleting this file")
    else:
        print("ℹ No existing token file (will authenticate when you run the script)")

    print()
    print("=" * 70)

    # Display issues
    if issues:
        print()
        print("ISSUES FOUND:")
        print("-" * 70)
        for issue in issues:
            print(issue)
        print()
        print("🔧 TO FIX:")
        print("1. Go to https://developer.whoop.com/")
        print("2. Create a new application")
        print("3. Get your real Client ID and Client Secret")
        print("4. Update your .env file with the real credentials")
        print("5. Add your redirect URI in the Whoop app settings")
        print()
        return False

    if warnings:
        print()
        print("WARNINGS:")
        print("-" * 70)
        for warning in warnings:
            print(warning)
        print()

    print("✅ Setup looks good! You can try running:")
    print()
    if redirect_uri.startswith("http://localhost"):
        print("   python3 whoop_simple.py")
    else:
        print("   python3 whoop_auth.py")
    print()
    print("=" * 70)
    return True

if __name__ == "__main__":
    verify_setup()
