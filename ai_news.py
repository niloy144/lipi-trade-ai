import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-flash-latest"


def summarize_news(title, description, language="বাংলা"):
    prompt = f"""You are a financial news analyst. Return ONLY valid JSON.

News Title: {title}
News Description: {description}

Return this structure:
{{
  "summary": "2-sentence summary in {language}",
  "sentiment": "bullish" or "bearish" or "neutral",
  "impact": "high" or "medium" or "low",
  "key_point": "One key takeaway in {language}"
}}
Return ONLY JSON, no markdown.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for attempt in range(3):
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            break
        elif response.status_code == 503:
            if attempt < 2:
                time.sleep(5)
            continue
        else:
            return {"error": f"API Error: {response.status_code}"}
    else:
        return {"error": "Server busy after 3 attempts"}

    ai_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    ai_text = ai_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(ai_text)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON", "raw": ai_text}

    # Test
test_news = {
    "title": "Bitcoin surges past $67,000 as ETF inflows hit record high",
    "description": "Institutional investors continue to pour money into Bitcoin ETFs."
}

print("Testing AI News Summarizer...")
print("=" * 60)
result = summarize_news(test_news["title"], test_news["description"], "বাংলা")
print(result)

# Test trade_analyzer import
from trade_analyzer import analyze_trade_screenshot
print("✅ Trade Analyzer import successful!")