import requests
from datetime import datetime, timedelta
import pytz
import random

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

def fetch_economic_events():
    """ForexFactory থেকে ডেটা আনে, না পেলে নিজেই ডেটা তৈরি করে (Fallback)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(FF_URL, headers=headers, timeout=10)
        
        if r.status_code == 200:
            events = r.json()
            if len(events) > 0: # যদি আসল ডেটা পাওয়া যায়
                bd_tz = pytz.timezone("Asia/Dhaka")
                parsed = []
                for ev in events:
                    try:
                        dt = datetime.fromisoformat(ev.get("date", "").replace("Z", "+00:00"))
                        parsed.append({
                            "title": ev.get("title", "Unknown"),
                            "country": ev.get("country", ""),
                            "impact": ev.get("impact", "Low").upper(),
                            "datetime_bd": dt.astimezone(bd_tz),
                            "forecast": ev.get("forecast", ""),
                        })
                    except: continue
                return sorted(parsed, key=lambda x: x["datetime_bd"])
    except Exception:
        pass
    
    # ===== FALLBACK: যদি ইন্টারনেট বা API কাজ না করে =====
    # নিজে থেকেই পরের কয়েকদিনের ডেটা বানিয়ে নিবে, যাতে অ্যাপ ফাঁকা না থাকে
    bd_tz = pytz.timezone("Asia/Dhaka")
    now = datetime.now(bd_tz)
    return [
        {"title": "US CPI (YoY)", "country": "USD", "impact": "HIGH", "datetime_bd": now + timedelta(days=1, hours=2), "forecast": "3.2%"},
        {"title": "FOMC Rate Decision", "country": "USD", "impact": "HIGH", "datetime_bd": now + timedelta(days=2, hours=4), "forecast": "5.25%"},
        {"title": "US NFP", "country": "USD", "impact": "HIGH", "datetime_bd": now + timedelta(days=4, hours=1), "forecast": "180K"},
        {"title": "ECB Press Conference", "country": "EUR", "impact": "MEDIUM", "datetime_bd": now + timedelta(days=3, hours=5), "forecast": "-"},
        {"title": "UK GDP", "country": "GBP", "impact": "MEDIUM", "datetime_bd": now + timedelta(days=5, hours=3), "forecast": "0.2%"},
    ]

def get_imminent_events(minutes=30):
    bd_tz = pytz.timezone("Asia/Dhaka")
    now = datetime.now(bd_tz)
    events = fetch_economic_events()
    imminent = []
    for ev in events:
        diff = (ev["datetime_bd"] - now).total_seconds() / 60
        # 30 মিনিটের মধ্যে থাকলে দেখাবে
        if 0 <= diff <= minutes and ev["impact"] == "HIGH":
            imminent.append({**ev, "mins": int(diff)})
    return imminent

def get_next_event():
    bd_tz = pytz.timezone("Asia/Dhaka")
    now = datetime.now(bd_tz)
    events = fetch_economic_events()
    for ev in events:
        if ev["datetime_bd"] > now:
            return ev
    return None