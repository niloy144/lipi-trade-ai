import os
import json
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ✅ Vision-capable model
MODEL = "gemini-flash-latest"


def analyze_trade_screenshot(image_bytes, notes="", language="বাংলা"):
    """
    Trade screenshot বিশ্লেষণ করে ৬ ভাষায়।
    FOMO entry, RR ratio, stop-loss placement ইত্যাদি detect করে।
    """
    
    # Image base64-এ convert
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = f"""You are a senior trading coach analyzing a trader's chart screenshot.

Trader's notes: {notes if notes else "No notes provided"}

Analyze this screenshot and detect technical and psychological mistakes. Look for:
- FOMO entries (entering after big move)
- Chasing candles
- Poor Risk-Reward ratio
- Bad stop-loss placement
- Over-leverage
- Trading against trend
- Missing confirmation

IMPORTANT: All text in "mistakes" and "suggestions" arrays MUST be in {language} language.

Return ONLY valid JSON with this exact structure:
{{
  "overall_rating": "excellent" or "good" or "average" or "poor",
  "mistakes": ["list of mistakes in {language}"],
  "suggestions": ["list of improvements in {language}"],
  "rr_estimate": "estimated risk-reward ratio like 1:1.5 or unknown",
  "confidence": 0.85
}}

Return ONLY JSON, no markdown, no extra text.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": b64_image
                    }
                }
            ]
        }]
    }

    # Retry logic
    for attempt in range(3):
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            break
        elif response.status_code == 503:
            if attempt < 2:
                time.sleep(5)
            continue
        else:
            return {"error": f"API Error: {response.status_code}", "details": response.text[:300]}
    else:
        return {"error": "Server busy (503) after 3 attempts. Try again later."}

    ai_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    ai_text = ai_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(ai_text)
    except json.JSONDecodeError:
        return {"error": "AI did not return valid JSON", "raw": ai_text}
   