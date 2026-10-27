
import feedparser
import requests
from urllib.parse import quote

def fetch_news(category="Crypto", limit=5):
    # ক্যাটাগরি অনুযায়ী নির্ভরযোগ্য RSS ফিড (Google News দেওয়া হয়েছে যাতে ক্লাউডে ব্লক না করে)
    feeds = {
        "Crypto": [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://news.google.com/rss/search?q=cryptocurrency+when:1d&hl=en-US&gl=US&ceid=US:en"
        ],
        "Forex": [
            "https://news.google.com/rss/search?q=forex+trading+OR+currency+market+when:1d&hl=en-US&gl=US&ceid=US:en"
        ],
        "Stocks": [
            "https://news.google.com/rss/search?q=stock+market+OR+wall+street+when:1d&hl=en-US&gl=US&ceid=US:en"
        ],
        "Global": [
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://news.google.com/rss/search?q=global+economy+when:1d&hl=en-US&gl=US&ceid=US:en"
        ]
    }

    urls = feeds.get(category, feeds["Crypto"])
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    articles = []
    
    for url in urls:
        if len(articles) >= limit:
            break
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries:
                    if len(articles) >= limit:
                        break
                    
                    # ডেসক্রিপশন ক্লিন করা
                    desc = entry.get("summary", "")
                    # Google News-এর ডেসক্রিপশনে অনেক সময় HTML ট্যাগ থাকে, সেগুলো পরিষ্কার করা
                    import re
                    desc = re.sub('<[^<]+?>', '', desc)
                    if len(desc) > 300:
                        desc = desc[:300] + "..."
                        
                    articles.append({
                        "source": entry.get("source", {}).get("title", feed.feed.get("title", "News")),
                        "title": entry.get("title", ""),
                        "description": desc,
                        "link": entry.get("link", ""),
                        "published": entry.get("published", "")
                    })
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            continue

    if not articles:
        articles.append({
            "source": "System",
            "title": "No news available at the moment.",
            "description": "Please try changing the category or check back later.",
            "link": "#",
            "published": ""
        })

    return articles[:limit]
