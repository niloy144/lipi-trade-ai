import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"Key: {api_key[:15]}...")

MODEL = "gemini-flash-latest"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
payload = {"contents": [{"parts": [{"text": "Say 'Hello Niloy' in Bengali."}]}]}

for attempt in range(10):
    print(f"\nAttempt {attempt + 1}/10...")
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {r.status_code}")

        if r.status_code == 200:
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\n✅ SUCCESS!")
            print(f"Response: {text}")
            break
        elif r.status_code == 503:
            print("⏳ Server busy — waiting 10 sec...")
            time.sleep(10)
        elif r.status_code == 429:
            print("❌ Daily quota exceeded. Try tomorrow.")
            break
        else:
            print(f"❌ {r.text[:200]}")
            break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)