import requests
import json

url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print("Fetching data...")
r = requests.get(url, headers=headers)
print(f"Status Code: {r.status_code}")

try:
    data = r.json()
    print(f"Total Events Found: {len(data)}")
    if len(data) > 0:
        print("First Event:", json.dumps(data[0], indent=2))
    else:
        print("API returned an EMPTY list [].")
except Exception as e:
    print(f"Error parsing JSON: {e}")