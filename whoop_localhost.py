#!/usr/bin/env python3
"""
Whoop OAuth Client - Based on working implementation from ald0405/whoop-data
Uses localhost callback server (no HTTPS domain needed for testing)
"""

import os
import json
import secrets
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Global variables for OAuth flow
oauth_result = {"code": None, "state": None, "error": None}
expected_state = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Whoop"""

    def do_GET(self):
        global oauth_result

        # Parse query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)

        if "code" in params:
            oauth_result["code"] = params["code"][0]
            oauth_result["state"] = params.get("state", [None])[0]

            # Send success page
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html>
            <head><title>Authorization Successful</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✓ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif "error" in params:
            oauth_result["error"] = params["error"][0]
            error_desc = params.get("error_description", ["Unknown error"])[0]

            # Send error page
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">✗ Authorization Failed</h1>
                <p><strong>Error:</strong> {oauth_result["error"]}</p>
                <p><strong>Description:</strong> {error_desc}</p>
                <hr>
                <p>Please close this window and check the terminal for instructions.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress HTTP log messages"""
        pass


class WhoopClient:
    """Whoop API Client with OAuth 2.0 authentication"""

    BASE_URL = "https://api.prod.whoop.com/developer"
    AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

    # Use localhost callback (like the working repo)
    CALLBACK_URL = "http://localhost:8765/callback"
    CALLBACK_PORT = 8765

    def __init__(self):
        self.client_id = os.getenv("WHOOP_CLIENT_ID")
        self.client_secret = os.getenv("WHOOP_CLIENT_SECRET")
        self.access_token = None
        self.refresh_token = None

        if not self.client_id or not self.client_secret:
            raise ValueError("Missing WHOOP_CLIENT_ID or WHOOP_CLIENT_SECRET in .env file")

    def authenticate(self):
        """Run the OAuth flow and get access token"""
        global oauth_result, expected_state

        # Reset result
        oauth_result = {"code": None, "state": None, "error": None}

        # Generate state for CSRF protection
        expected_state = secrets.token_urlsafe(32)

        # Build authorization URL
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.CALLBACK_URL,
            "scope": "read:recovery read:sleep read:workout read:profile read:body_measurement read:cycles",
            "state": expected_state
        }
        auth_url = f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

        print(f"\n🌐 Starting local callback server on port {self.CALLBACK_PORT}...")
        print("🔓 Opening Whoop authorization page in your browser...\n")

        # Start local server
        server = HTTPServer(("localhost", self.CALLBACK_PORT), OAuthCallbackHandler)

        # Run server in background
        server_thread = threading.Thread(target=server.handle_request)
        server_thread.daemon = True
        server_thread.start()

        # Open browser
        try:
            webbrowser.open(auth_url)
            print("✓ Browser opened")
        except:
            print("⚠ Could not open browser automatically")
            print(f"\nPlease visit this URL:\n{auth_url}\n")

        print("⏳ Waiting for authorization...\n")

        # Wait for callback
        server_thread.join(timeout=300)  # 5 minute timeout

        # Shutdown server
        try:
            server.shutdown()
        except:
            pass

        # Check for errors
        if oauth_result["error"]:
            raise Exception(f"OAuth error: {oauth_result['error']}")

        if not oauth_result["code"]:
            raise Exception("No authorization code received. Please try again.")

        # Validate state
        if oauth_result["state"] != expected_state:
            raise Exception("State mismatch - possible CSRF attack!")

        # Exchange code for token
        print("🔄 Exchanging authorization code for access token...")
        token_data = self._exchange_code_for_token(oauth_result["code"])

        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")

        # Save tokens
        self._save_tokens(token_data)
        print("✓ Authentication successful!\n")

        return token_data

    def _exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.CALLBACK_URL
        }

        response = requests.post(self.TOKEN_URL, data=data)

        if response.status_code != 200:
            print(f"\n✗ Token exchange failed: {response.status_code}")
            print(f"Response: {response.text}\n")
            response.raise_for_status()

        return response.json()

    def _save_tokens(self, token_data):
        """Save tokens to file"""
        with open(".whoop_tokens.json", "w") as f:
            json.dump(token_data, f, indent=2)
        print("✓ Tokens saved to .whoop_tokens.json")

    def load_tokens(self):
        """Load tokens from file"""
        try:
            with open(".whoop_tokens.json", "r") as f:
                token_data = json.load(f)
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                return True
        except FileNotFoundError:
            return False

    def _make_request(self, endpoint, params=None):
        """Make authenticated API request"""
        if not self.access_token:
            raise ValueError("Not authenticated. Please run authenticate() first.")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.BASE_URL}{endpoint}"

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"\n✗ API request failed: {response.status_code}")
            print(f"Response: {response.text}\n")

        response.raise_for_status()
        return response.json()

    # API Methods
    def get_profile(self):
        """Get user profile"""
        return self._make_request("/v1/user/profile/basic")

    def get_recovery(self, start_date=None, end_date=None, limit=25):
        """Get recovery data"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/recovery", params)

    def get_sleep(self, start_date=None, end_date=None, limit=25):
        """Get sleep data"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/activity/sleep", params)

    def get_workouts(self, start_date=None, end_date=None, limit=25):
        """Get workout data"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/activity/workout", params)

    def get_cycles(self, start_date=None, end_date=None, limit=25):
        """Get cycle data"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/cycle", params)

    def get_all_data(self, days=30):
        """Get all data for specified number of days"""
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=days)).isoformat()

        print(f"\n📊 Fetching Whoop data from {start_date} to {end_date}...\n")

        data = {
            "profile": None,
            "recovery": None,
            "sleep": None,
            "workouts": None,
            "cycles": None,
            "date_range": {"start": start_date, "end": end_date}
        }

        print("  → Fetching profile...")
        data["profile"] = self.get_profile()

        print("  → Fetching recovery data...")
        data["recovery"] = self.get_recovery(start_date, end_date)

        print("  → Fetching sleep data...")
        data["sleep"] = self.get_sleep(start_date, end_date)

        print("  → Fetching workouts...")
        data["workouts"] = self.get_workouts(start_date, end_date)

        print("  → Fetching cycles...")
        data["cycles"] = self.get_cycles(start_date, end_date)

        print("\n✓ All data fetched successfully!\n")

        return data


def save_data(data, filename="whoop_data.json"):
    """Save data to JSON file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✓ Data saved to {filename}")


if __name__ == "__main__":
    print("=" * 70)
    print(" " * 15 + "Whoop Data Client (Localhost Version)")
    print("=" * 70)

    client = WhoopClient()

    # Try to load existing tokens
    if not client.load_tokens():
        print("\n⚠ No saved tokens found. Starting authentication...\n")
        try:
            client.authenticate()
        except Exception as e:
            print(f"\n✗ Authentication failed: {e}\n")
            print("💡 Make sure you have:")
            print("  1. Real WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET in .env")
            print("  2. Registered http://localhost:8765/callback in your Whoop app")
            print("  3. Port 8765 is not in use\n")
            exit(1)
    else:
        print("\n✓ Loaded existing tokens\n")

    # Fetch data
    try:
        data = client.get_all_data(days=30)
        save_data(data)

        # Print summary
        print("\n" + "=" * 70)
        print(" " * 25 + "DATA SUMMARY")
        print("=" * 70)

        if data["profile"]:
            print(f"User ID: {data['profile'].get('user_id', 'N/A')}")
            print(f"Email: {data['profile'].get('email', 'N/A')}")

        for key in ["recovery", "sleep", "workouts", "cycles"]:
            if data.get(key):
                count = len(data[key].get("records", []))
                print(f"{key.title()}: {count} records")

        print("=" * 70)
        print("\n✓ Success!\n")

    except Exception as e:
        print(f"\n✗ Error: {e}\n")
        if "401" in str(e) or "403" in str(e):
            print("💡 Try deleting .whoop_tokens.json and re-authenticating\n")
