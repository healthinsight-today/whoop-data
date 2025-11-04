#!/usr/bin/env python3
"""
Simple Whoop API Client for HealthInsightToday.com with automatic OAuth flow
"""

import os
import json
import requests
import secrets
import webbrowser
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, Dict
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Load environment variables
load_dotenv()

# Global variable to store the auth code
auth_code_result = {"code": None, "error": None}


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Whoop"""

    def do_GET(self):
        """Handle GET request from OAuth redirect"""
        global auth_code_result

        # Parse the query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)

        if "code" in params:
            auth_code_result["code"] = params["code"][0]
            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            success_html = """
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✓ Authorization Successful!</h1>
                <p>You can close this window and return to your terminal.</p>
                <p>The Whoop client will now fetch your data...</p>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
        elif "error" in params:
            auth_code_result["error"] = params["error"][0]
            # Send error response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error_html = f"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">✗ Authorization Failed</h1>
                <p>Error: {params.get('error_description', ['Unknown error'])[0]}</p>
                <p>Please return to your terminal and try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


class WhoopClient:
    """Simple client for interacting with Whoop API v2"""

    BASE_URL = "https://api.prod.whoop.com/developer"
    AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

    def __init__(self):
        """Initialize the Whoop client with credentials from .env file"""
        self.client_id = os.getenv("WHOOP_CLIENT_ID")
        self.client_secret = os.getenv("WHOOP_CLIENT_SECRET")
        self.redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8080/callback")
        self.access_token = None
        self.refresh_token = None
        self.state = None

        if not self.client_id or not self.client_secret:
            raise ValueError("Missing WHOOP_CLIENT_ID or WHOOP_CLIENT_SECRET in .env file")

    def _generate_state(self) -> str:
        """Generate a secure random state parameter for OAuth2"""
        return secrets.token_urlsafe(32)

    def get_authorization_url(self) -> str:
        """Generate the authorization URL for user to authenticate"""
        self.state = self._generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": self.state,
            "scope": "read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement"
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def start_oauth_flow(self) -> str:
        """
        Start the OAuth flow with automatic callback handling

        Returns:
            Authorization code from Whoop
        """
        global auth_code_result
        auth_code_result = {"code": None, "error": None}

        # Start local server to receive callback
        server_port = 8080
        server = HTTPServer(("localhost", server_port), CallbackHandler)

        print(f"\n🌐 Starting local server on http://localhost:{server_port}")
        print("⏳ Waiting for OAuth callback...\n")

        # Run server in background thread
        server_thread = threading.Thread(target=server.handle_request)
        server_thread.daemon = True
        server_thread.start()

        # Open authorization URL in browser
        auth_url = self.get_authorization_url()
        print(f"🔓 Opening authorization URL in your browser...\n")
        print(f"If the browser doesn't open automatically, visit:\n{auth_url}\n")

        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"⚠ Could not open browser: {e}")

        # Wait for callback
        print("👉 Please authorize the application in your browser...")
        server_thread.join(timeout=300)  # Wait up to 5 minutes

        # Shutdown server
        try:
            server.shutdown()
        except:
            pass

        if auth_code_result["error"]:
            raise Exception(f"OAuth error: {auth_code_result['error']}")

        if not auth_code_result["code"]:
            raise Exception("Did not receive authorization code. Please try again.")

        return auth_code_result["code"]

    def authenticate(self, auth_code: str) -> Dict:
        """
        Exchange authorization code for access token

        Args:
            auth_code: The authorization code from the callback

        Returns:
            Token response containing access_token and refresh_token
        """
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }

        print("\n🔄 Exchanging authorization code for access token...")
        response = requests.post(self.TOKEN_URL, data=data)

        if response.status_code != 200:
            print(f"\n✗ Token exchange failed: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")

        # Save tokens to file
        self._save_tokens(token_data)

        return token_data

    def _save_tokens(self, token_data: Dict):
        """Save tokens to a file for reuse"""
        with open(".whoop_tokens.json", "w") as f:
            json.dump(token_data, f)
        print("✓ Tokens saved to .whoop_tokens.json")

    def load_tokens(self) -> bool:
        """
        Load tokens from file if they exist

        Returns:
            True if tokens were loaded successfully, False otherwise
        """
        try:
            with open(".whoop_tokens.json", "r") as f:
                token_data = json.load(f)
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                return True
        except FileNotFoundError:
            return False

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make an authenticated request to the Whoop API

        Args:
            endpoint: API endpoint (e.g., '/v1/user/profile/basic')
            params: Optional query parameters

        Returns:
            JSON response from the API
        """
        if not self.access_token:
            raise ValueError("No access token available. Please authenticate first.")

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"\n✗ API request failed: {response.status_code}")
            print(f"Response: {response.text}")

        response.raise_for_status()
        return response.json()

    def get_profile(self) -> Dict:
        """Get user profile information"""
        return self._make_request("/v1/user/profile/basic")

    def get_body_measurement(self) -> Dict:
        """Get user's body measurements"""
        return self._make_request("/v1/user/measurement/body")

    def get_cycles(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """Get physiological cycles"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/cycle", params=params)

    def get_recovery(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """Get recovery data"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/recovery", params=params)

    def get_sleep(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """Get sleep data"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/activity/sleep", params=params)

    def get_workouts(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """Get workout data"""
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return self._make_request("/v1/activity/workout", params=params)

    def get_all_data(self, days: int = 30) -> Dict:
        """
        Get all available data for the specified number of days

        Args:
            days: Number of days to retrieve data for (default 30)

        Returns:
            Dictionary containing all data types
        """
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=days)).isoformat()

        print(f"\n📊 Fetching Whoop data from {start_date} to {end_date}...")

        data = {
            "profile": None,
            "body_measurement": None,
            "cycles": None,
            "recovery": None,
            "sleep": None,
            "workouts": None,
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }

        try:
            print("  → Fetching profile...")
            data["profile"] = self.get_profile()

            print("  → Fetching body measurements...")
            try:
                data["body_measurement"] = self.get_body_measurement()
            except Exception as e:
                print(f"    ⚠ Could not fetch body measurements: {e}")

            print("  → Fetching cycles...")
            data["cycles"] = self.get_cycles(start_date, end_date)

            print("  → Fetching recovery data...")
            data["recovery"] = self.get_recovery(start_date, end_date)

            print("  → Fetching sleep data...")
            data["sleep"] = self.get_sleep(start_date, end_date)

            print("  → Fetching workouts...")
            data["workouts"] = self.get_workouts(start_date, end_date)

            print("✓ All data fetched successfully!\n")

        except Exception as e:
            print(f"✗ Error fetching data: {e}")
            raise

        return data


def save_data_to_file(data: Dict, filename: str = "whoop_data.json"):
    """Save fetched data to a JSON file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✓ Data saved to {filename}")


if __name__ == "__main__":
    print("=" * 70)
    print(" " * 10 + "Whoop Data Client for HealthInsightToday.com")
    print("=" * 70)

    # Initialize client
    client = WhoopClient()

    # Try to load existing tokens
    if not client.load_tokens():
        print("\n⚠ No saved tokens found. Starting authentication flow...\n")

        try:
            # Start automatic OAuth flow
            auth_code = client.start_oauth_flow()

            # Exchange code for tokens
            client.authenticate(auth_code)
            print("✓ Authentication successful!\n")

        except KeyboardInterrupt:
            print("\n\n⚠ Authentication cancelled by user.")
            exit(0)
        except Exception as e:
            print(f"\n✗ Authentication failed: {e}")
            print("\nPlease check your credentials in .env file and try again.")
            exit(1)
    else:
        print("✓ Loaded existing tokens from file\n")

    # Fetch data
    try:
        data = client.get_all_data(days=30)
        save_data_to_file(data)

        # Print summary
        print("\n" + "=" * 70)
        print(" " * 25 + "DATA SUMMARY")
        print("=" * 70)

        if data["profile"]:
            print(f"User ID: {data['profile'].get('user_id', 'N/A')}")
            print(f"Email: {data['profile'].get('email', 'N/A')}")

        if data["cycles"]:
            print(f"Cycles: {len(data['cycles'].get('records', []))} records")

        if data["recovery"]:
            print(f"Recovery: {len(data['recovery'].get('records', []))} records")

        if data["sleep"]:
            print(f"Sleep: {len(data['sleep'].get('records', []))} records")

        if data["workouts"]:
            print(f"Workouts: {len(data['workouts'].get('records', []))} records")

        print("=" * 70)
        print("\n✓ Success! Your Whoop data has been saved to whoop_data.json")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. If authentication error: Delete .whoop_tokens.json and run again")
        print("  2. Check your credentials in .env file")
        print("  3. Make sure you have data in your Whoop account for the date range")
