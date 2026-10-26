import os
import requests
from dotenv import load_dotenv

# .env ফাইল থেকে টোকেন লোড করা
load_dotenv()

def send_telegram_message(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ Error: .env ফাইলে টোকেন বা চ্যাট আইডি পাওয়া যায়নি!")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # মেসেজ পাঠানোর ডেটা
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ সফলভাবে টেলিগ্রামে মেসেজ পাঠানো হয়েছে!")
        else:
            print(f"❌ মেসেজ পাঠাতে সমস্যা হয়েছে। Status Code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing Telegram Alert...")
    send_telegram_message("🚀 আসসালামু আলাইকুম নিলয় ভাই! এটি Lipi Trade AI থেকে পাঠানো একটি টেস্ট মেসেজ। সব ঠিকঠাক কাজ করছে!")