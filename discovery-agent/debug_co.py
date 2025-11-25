import requests
from datetime import datetime, timedelta

def debug_co_api():
    base_url = "https://www.dallasopendata.com/resource/dryn-sntn.json"
    
    # Test 1: Just get latest 5 records regardless of date/filter
    print("--- Test 1: Fetching latest 5 records ---")
    params = {
        "$limit": 5,
        "$order": "date_issued DESC"
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        print(f"Found {len(data)} records.")
        if data:
            print("Sample Date:", data[0].get('date_issued'))
            print("Sample Land Use:", data[0].get('land_use'))
            print("Sample Sq Ft:", data[0].get('sq_ft'))
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Check valid dates
    print("\n--- Test 3: Checking for ANY valid dates ---")
    params = {
        "$where": "date_issued IS NOT NULL",
        "$limit": 5,
        "$order": "date_issued DESC"
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        print(f"Found {len(data)} records with dates.")
        if data:
            print("Most Recent Date:", data[0].get('date_issued'))
    except Exception as e:
        print(f"Error: {e}")


def debug_permits_api():
    base_url = "https://www.dallasopendata.com/resource/e7gq-4sah.json"
    print("\n--- Checking Building Permits Dataset (e7gq-4sah) ---")
    
    params = {
        "$where": "issued_date IS NOT NULL",
        "$limit": 5,
        "$order": "issued_date DESC"
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        if data:
            print("Most Recent Permit Date:", data[0].get('issued_date'))
            print("Sample Record:", data[0])
        else:
            print("No records found.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # debug_co_api() # Skip the stale one
    debug_permits_api()
