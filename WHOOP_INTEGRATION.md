# Whoop API Integration for HealthInsightToday.com

A simple, clean Python client for pulling data from the Whoop API v2.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_whoop.txt
```

### 2. Configure Credentials

Your credentials are already set in the `.env` file:

```env
WHOOP_CLIENT_ID=76450-ba57-400e-a7a4-27494d51b842
WHOOP_CLIENT_SECRET=9a24e6812963262f2a932907603626578592eadee2c28129a9313f8cd2d0
WHOOP_REDIRECT_URI=http://localhost:8000/callback
```

### 3. Authenticate and Pull Data

Run the main script:

```bash
python whoop_client.py
```

This will:
1. Open your browser to authenticate with Whoop
2. Ask you to paste the authorization code
3. Fetch all your data (profile, recovery, sleep, workouts, cycles)
4. Save everything to `whoop_data.json`

## Usage Examples

### Basic Usage (All Data)

```python
from whoop_client import WhoopClient, save_data_to_file

# Initialize client
client = WhoopClient()

# Load saved tokens (or authenticate first)
client.load_tokens()

# Get all data for last 30 days
data = client.get_all_data(days=30)

# Save to file
save_data_to_file(data, "my_whoop_data.json")
```

### Get Specific Data Types

```python
from whoop_client import WhoopClient
from datetime import datetime, timedelta

client = WhoopClient()
client.load_tokens()

# Get last 7 days
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

# Get recovery data
recovery = client.get_recovery(
    start_date=start_date.isoformat(),
    end_date=end_date.isoformat()
)

# Get sleep data
sleep = client.get_sleep(
    start_date=start_date.isoformat(),
    end_date=end_date.isoformat()
)

# Get workouts
workouts = client.get_workouts(
    start_date=start_date.isoformat(),
    end_date=end_date.isoformat()
)

# Get cycles (physiological data)
cycles = client.get_cycles(
    start_date=start_date.isoformat(),
    end_date=end_date.isoformat()
)

# Get user profile
profile = client.get_profile()

# Get body measurements
body = client.get_body_measurement()
```

## Available Methods

### `WhoopClient` Class

- **`get_profile()`** - Get user profile information
- **`get_body_measurement()`** - Get body measurements (height, weight, etc.)
- **`get_cycles(start_date, end_date, limit)`** - Get physiological cycles
- **`get_recovery(start_date, end_date, limit)`** - Get recovery data (HRV, resting HR, etc.)
- **`get_sleep(start_date, end_date, limit)`** - Get sleep data
- **`get_workouts(start_date, end_date, limit)`** - Get workout data
- **`get_all_data(days)`** - Get all data types for specified number of days

## Data Structure

The fetched data is saved in JSON format with the following structure:

```json
{
  "profile": {
    "user_id": "...",
    "email": "...",
    "first_name": "...",
    "last_name": "..."
  },
  "body_measurement": { ... },
  "cycles": {
    "records": [...]
  },
  "recovery": {
    "records": [
      {
        "cycle_id": "...",
        "sleep_id": "...",
        "user_id": "...",
        "created_at": "2024-01-01T12:00:00.000Z",
        "updated_at": "2024-01-01T12:00:00.000Z",
        "score": {
          "user_calibrating": false,
          "recovery_score": 67,
          "resting_heart_rate": 55,
          "hrv_rmssd_milli": 45.2,
          "spo2_percentage": 96.5,
          "skin_temp_celsius": 33.8
        }
      }
    ]
  },
  "sleep": {
    "records": [...]
  },
  "workouts": {
    "records": [...]
  },
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

## Authentication Flow

1. First run: You'll need to authenticate via Whoop's OAuth2 flow
2. Your browser will open to Whoop's authorization page
3. After authorizing, copy the `code` parameter from the callback URL
4. Paste the code when prompted
5. Tokens are saved to `.whoop_tokens.json` for future use

## Example Scripts

Run the example script to see all features:

```bash
python example_usage.py
```

This demonstrates:
- Getting user profile
- Fetching recovery data
- Fetching sleep data
- Fetching workout data
- Getting all data and saving to file

## Troubleshooting

### "No access token available"
Run `python whoop_client.py` to authenticate first.

### "Invalid token" or authentication errors
Delete `.whoop_tokens.json` and run authentication again:
```bash
rm .whoop_tokens.json
python whoop_client.py
```

### Can't find data
Make sure you have data in your Whoop account for the date range you're querying.

## API Scopes

The client requests the following scopes:
- `read:recovery` - Recovery data
- `read:cycles` - Physiological cycles
- `read:sleep` - Sleep data
- `read:workout` - Workout data
- `read:profile` - User profile
- `read:body_measurement` - Body measurements

## Notes

- All dates should be in ISO format: `YYYY-MM-DD`
- Maximum limit per request: 50 records
- Tokens are automatically saved and reused
- Data is returned in JSON format

## For HealthInsightToday.com

This integration provides clean, structured access to Whoop data that can be:
- Stored in a database
- Analyzed for health insights
- Displayed on dashboards
- Used for trend analysis
- Exported to other formats

The simple design makes it easy to integrate into any workflow or application.
