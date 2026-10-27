import feedparser
import requests
import urllib.parse

def fetch_news(category="Crypto", limit=5):
    # ক্যাটাগরি অনুযায়ী নির্ভরযোগ্য RSS ফিডের লিস্ট
    feeds = {
        "Crypto": [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss"
        ],
        "Forex": [
            "https://www.fxstreet.com/rss/news",
            "https://www.dailyfx.com/feeds/all"
        ],
        "Stocks": [
            "https://finance.yahoo.com/news/rssindex",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html"
        ],
        "Global": [
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"
        ]
    }

    # ডিফল্ট হিসেবে Crypto ফিড নেবে
    urls = feeds.get(category, feeds["Crypto"])
    
    # ব্রাউজারের মতো একটি হেডার পাঠানো, যাতে ওয়েবসাইট বট ভেবে ব্লক না করে
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    articles = []
    
    for url in urls:
        try:
            # রিকোয়েস্ট পাঠানো
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries:
                    if len(articles) >= limit:
                        break
                    
                    # নিউজের ডেসক্রিপশন পরিষ্কার করা
                    desc = entry.get("summary", "")
                    if len(desc) > 300:
                        desc = desc[:300] + "..."
                        
                    articles.append({
                        "source": feed.feed.get("title", "News"),
                        "title": entry.get("title", ""),
                        "description": desc,
                        "link": entry.get("link", ""),
                        "published": entry.get("published", "")
                    })
            
            # যদি পর্যাপ্ত নিউজ পাওয়া যায়, তবে লুপ থামিয়ে দেবে
            if len(articles) >= limit:
                break
                
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            continue

    return articles[:limit]
