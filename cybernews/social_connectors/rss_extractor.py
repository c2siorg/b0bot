import feedparser
import warnings
from datetime import datetime
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from cybernews.performance import Performance
from cybernews.sorting import Sorting

# Suppress BeautifulSoup warning for URL-like strings from some feed summaries
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

class RSSExtractor(Performance):
    def __init__(self):
        super().__init__()
        self.sorting = Sorting()

    def process_feeds(self, feeds: list) -> list:
        news_data = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    # Some feeds (e.g. Mastodon) have entries without title or link — skip them
                    title = entry.get('title', '').strip()
                    link = entry.get('link', '').strip()
                    if not title or not link:
                        continue

                    # Clean up RSS bodies which often contain embedded HTML
                    soup = BeautifulSoup(entry.get('summary', '') or entry.get('description', ''), 'lxml')
                    body_text = soup.get_text(separator=' ', strip=True)

                    if self.spam_content_check(title + " " + body_text):
                        continue

                    # Try to parse published date, fallback to 'N/A'
                    date_str = "N/A"
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        dt = datetime(*entry.published_parsed[:6])
                        date_str = dt.strftime("%B %d, %Y")

                    item = {
                        "id": self.sorting.ordering_date(date_str) if date_str != "N/A" else 0,
                        "headlines": title,
                        "author": entry.get('author', 'N/A'),
                        "fullNews": body_text[:500] + "..." if len(body_text) > 500 else body_text,
                        "newsURL": link,
                        "newsImgURL": "N/A",
                        "newsDate": date_str
                    }
                    news_data.append(item)
            except Exception as e:
                print(f"[RSS Error] Failed to parse {feed_url}: {e}")

        # Basic deduplication across feeds
        seen = set()
        unique = []
        for item in news_data:
            if item["newsURL"] not in seen:
                seen.add(item["newsURL"])
                unique.append(item)
                
        return self.sorting.ordering_news(unique)
