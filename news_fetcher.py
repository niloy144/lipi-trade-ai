import feedparser
from datetime import datetime


# Free RSS Feeds — no API key needed
NEWS_SOURCES = {
    "Crypto": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
    ],
    "Stocks": [
        {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
    ],
    "Forex": [
        {"name": "FXStreet", "url": "https://www.fxstreet.com/rss/news"},
    ],
    "Global": [
        {"name": "BBC Business", "url": "http://feeds.bbci.co.uk/news/business/rss.xml"},
        {"name": "CNBC", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    ],
}


def fetch_news(category="Crypto", limit=5):
    """RSS feeds থেকে real news আনে।"""
    sources = NEWS_SOURCES.get(category, NEWS_SOURCES["Crypto"])
    all_articles = []

    for source in sources:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:limit]:
                all_articles.append({
                    "source": source["name"],
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", "")[:500],
                    "link": entry.get("link", "#"),
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")
            continue

    return all_articles[:limit * 2]

# Test
if __name__ == "__main__":
    news = fetch_news("Crypto", limit=3)
    print(f"Found {len(news)} articles:\n")
    for i, n in enumerate(news, 1):
        print(f"{i}. [{n['source']}] {n['title'][:80]}...")
        print(f"   Link: {n['link']}")
        print()