import requests
import json

def probe_dataset(dataset_id, name):
    url = f"https://www.dallasopendata.com/resource/{dataset_id}.json?$limit=1"
    print(f"\n--- Probing {name} ({dataset_id}) ---")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data:
                print("Success! Columns found:")
                print(json.dumps(list(data[0].keys()), indent=2))
                print("\nSample Data:")
                print(json.dumps(data[0], indent=2))
            else:
                print("Success, but empty dataset.")
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

probe_dataset("e7gq-4sah", "Building Permits")
probe_dataset("dryn-sntn", "Certificates of Occupancy")
