#!/usr/bin/env python3
"""
Example script showing how to use the Whoop Client
"""

from whoop_client import WhoopClient, save_data_to_file
from datetime import datetime, timedelta

def main():
    # Initialize the client
    client = WhoopClient()

    # Load existing tokens or authenticate
    if not client.load_tokens():
        print("No tokens found. Please run whoop_client.py first to authenticate.")
        return

    print("✓ Authenticated with Whoop API\n")

    # Example 1: Get user profile
    print("=" * 60)
    print("EXAMPLE 1: Getting User Profile")
    print("=" * 60)
    profile = client.get_profile()
    print(f"User ID: {profile.get('user_id')}")
    print(f"Email: {profile.get('email')}")
    print(f"First Name: {profile.get('first_name')}")
    print(f"Last Name: {profile.get('last_name')}\n")

    # Example 2: Get last 7 days of recovery data
    print("=" * 60)
    print("EXAMPLE 2: Getting Last 7 Days of Recovery")
    print("=" * 60)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    recovery = client.get_recovery(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

    if recovery.get('records'):
        print(f"Found {len(recovery['records'])} recovery records\n")
        for record in recovery['records'][:3]:  # Show first 3
            score = record.get('score', {})
            print(f"Date: {record.get('created_at', 'N/A')}")
            print(f"  Recovery Score: {score.get('recovery_score', 'N/A')}")
            print(f"  HRV: {score.get('hrv_rmssd_milli', 'N/A')} ms")
            print(f"  Resting HR: {score.get('resting_heart_rate', 'N/A')} bpm\n")
    else:
        print("No recovery records found\n")

    # Example 3: Get sleep data
    print("=" * 60)
    print("EXAMPLE 3: Getting Sleep Data")
    print("=" * 60)
    sleep = client.get_sleep(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

    if sleep.get('records'):
        print(f"Found {len(sleep['records'])} sleep records\n")
        for record in sleep['records'][:3]:  # Show first 3
            score = record.get('score', {})
            print(f"Sleep Date: {record.get('start', 'N/A')}")
            print(f"  Sleep Score: {score.get('stage_summary', {}).get('total_in_bed_time_milli', 'N/A')}")
            print(f"  Sleep Duration: {score.get('stage_summary', {}).get('total_sleep_time_milli', 'N/A')} ms\n")
    else:
        print("No sleep records found\n")

    # Example 4: Get workouts
    print("=" * 60)
    print("EXAMPLE 4: Getting Workout Data")
    print("=" * 60)
    workouts = client.get_workouts(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

    if workouts.get('records'):
        print(f"Found {len(workouts['records'])} workout records\n")
        for record in workouts['records'][:3]:  # Show first 3
            print(f"Workout: {record.get('sport_id', 'Unknown')}")
            print(f"  Start: {record.get('start', 'N/A')}")
            print(f"  Strain: {record.get('score', {}).get('strain', 'N/A')}\n")
    else:
        print("No workout records found\n")

    # Example 5: Get all data for last 30 days and save to file
    print("=" * 60)
    print("EXAMPLE 5: Getting ALL Data (30 days)")
    print("=" * 60)
    all_data = client.get_all_data(days=30)
    save_data_to_file(all_data, "whoop_data_30days.json")

    print("\n✓ All examples completed successfully!")

if __name__ == "__main__":
    main()
