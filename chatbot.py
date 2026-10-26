import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

# Working Groq model — fastest + most reliable
MODEL = "qwen/qwen3.8-27b"  

client = Groq(api_key=groq_key)


def ask_trading_ai(question, language="বাংলা", context=None):
    """AI Trading Chatbot — powered by Groq (Ma Lipi Trade AI)"""
    ctx_text = ""
    if context:
        ctx_text = (
            f"\nMarket Context: BTC={context.get('BTCUSD','N/A')}, "
            f"Gold={context.get('XAUUSD','N/A')}\n"
        )

    prompt = f"""You are Lipi Trade AI, an expert trading assistant built by Niloy for Ma Lipi.

CRITICAL RULES:
1. Answer ONLY in {language} language.
2. Be honest — never guarantee profits.
3. Always mention risks when suggesting any direction.
4. Give reasoning based on the market context provided.
5. Keep answers short: 3-5 sentences maximum.
6. If unsure, say so clearly.
{ctx_text}
User Question: {question}

Answer in {language}:"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            reply = response.choices[0].message.content.strip()
            return {"reply": reply}

        except Exception as e:
            err = str(e)
            if "rate_limit" in err.lower() or "429" in err:
                time.sleep(5)
                continue
            if attempt < 2:
                time.sleep(2)
                continue
            return {"error": f"AI Error: {err[:200]}"}

    return {"error": "Rate limit exceeded. Please wait a moment."}