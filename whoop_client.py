#!/usr/bin/env python3
"""
Simple Whoop API Client for HealthInsightToday.com
Handles OAuth2 authentication and data retrieval from Whoop API
"""

import os
import json
import requests
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, Dict, List
import webbrowser
from urllib.parse import urlencode

# Load environment variables
load_dotenv()


class WhoopClient:
    """Simple client for interacting with Whoop API v2"""

    BASE_URL = "https://api.prod.whoop.com/developer"
    AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

    def __init__(self):
        """Initialize the Whoop client with credentials from .env file"""
        self.client_id = os.getenv("WHOOP_CLIENT_ID")
        self.client_secret = os.getenv("WHOOP_CLIENT_SECRET")
        self.redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8000/callback")
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
        # Generate and save state for CSRF protection
        self.state = self._generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": self.state,
            "scope": "read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement"
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

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

        response = requests.post(self.TOKEN_URL, data=data)
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
        response.raise_for_status()

        return response.json()

    def get_profile(self) -> Dict:
        """Get user profile information"""
        return self._make_request("/v1/user/profile/basic")

    def get_body_measurement(self) -> Dict:
        """Get user's body measurements"""
        return self._make_request("/v1/user/measurement/body")

    def get_cycles(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """
        Get physiological cycles

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Number of records to return (default 25, max 50)
        """
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        return self._make_request("/v1/cycle", params=params)

    def get_recovery(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """
        Get recovery data

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Number of records to return (default 25, max 50)
        """
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        return self._make_request("/v1/recovery", params=params)

    def get_sleep(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """
        Get sleep data

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Number of records to return (default 25, max 50)
        """
        params = {"limit": limit}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        return self._make_request("/v1/activity/sleep", params=params)

    def get_workouts(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 25) -> Dict:
        """
        Get workout data

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Number of records to return (default 25, max 50)
        """
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

        print(f"\nFetching Whoop data from {start_date} to {end_date}...")

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
            data["body_measurement"] = self.get_body_measurement()

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
    print("=" * 60)
    print("Whoop Data Client for HealthInsightToday.com")
    print("=" * 60)

    # Initialize client
    client = WhoopClient()

    # Try to load existing tokens
    if not client.load_tokens():
        print("\n⚠ No saved tokens found. Starting authentication flow...")
        print("\n1. Visit this URL to authorize the application:")
        auth_url = client.get_authorization_url()
        print(f"\n{auth_url}\n")

        # Try to open in browser
        try:
            webbrowser.open(auth_url)
            print("✓ Authorization URL opened in your browser")
        except:
            print("⚠ Could not open browser automatically")

        print("\n2. After authorizing, copy the 'code' parameter from the callback URL")
        auth_code = input("\nEnter the authorization code: ").strip()

        # Exchange code for tokens
        print("\nExchanging code for access token...")
        client.authenticate(auth_code)
        print("✓ Authentication successful!")
    else:
        print("✓ Loaded existing tokens from file")

    # Fetch data
    try:
        data = client.get_all_data(days=30)
        save_data_to_file(data)

        # Print summary
        print("\n" + "=" * 60)
        print("DATA SUMMARY")
        print("=" * 60)
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

        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nIf the error is authentication-related, try deleting .whoop_tokens.json and running again.")
