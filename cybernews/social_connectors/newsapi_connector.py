import os
from datetime import datetime
from cybernews.performance import Performance
from cybernews.sorting import Sorting

# NOTE: Requires NEWSAPI_KEY in your .env
# Get a free key (100 requests/day) instantly at: https://newsapi.org/register
# No credit card required.

class NewsAPIConnector(Performance):
    """
    Optional connector that uses NewsAPI.org to fetch real cybersecurity
    news articles from 150,000+ verified news sources.

    Activation: Set NEWSAPI_KEY in your .env file.
    If the key is absent, this connector silently skips and returns an empty list.
    """

    FALLBACK_QUERY = "cybersecurity OR infosec OR CVE OR data breach OR malware"
    MAX_RESULTS = 20

    def __init__(self):
        super().__init__()
        self.sorting = Sorting()
        self.is_configured = False
        self._client = None

        api_key = os.environ.get("NEWSAPI_KEY")
        if not api_key:
            print("[NewsAPI Connector] Skipping: NEWSAPI_KEY not found in env.")
            return

        try:
            from newsapi import NewsApiClient
            self._client = NewsApiClient(api_key=api_key)
            self.is_configured = True
            print("[NewsAPI Connector] Initialized successfully.")
        except ImportError:
            print("[NewsAPI Connector] Skipping: 'newsapi-python' not installed. Run: pip install newsapi-python")
        except Exception as e:
            print(f"[NewsAPI Connector] Initialization failed: {e}")

    def extract(self, query: str = None) -> list:
        """
        Fetches recent cybersecurity articles from NewsAPI.org.
        Args:
            query: Category-specific search string from social_sources.json api_queries.
                   Falls back to FALLBACK_QUERY if not provided.
        Returns a list of standardized news dictionaries.
        """
        if not self.is_configured:
            return []

        search_query = query or self.FALLBACK_QUERY
        news_data = []
        try:
            response = self._client.get_everything(
                q=search_query,
                language="en",
                sort_by="publishedAt",
                page_size=self.MAX_RESULTS
            )

            for article in response.get("articles", []):
                title = (article.get("title") or "").strip()
                description = (article.get("description") or "").strip()
                content = (article.get("content") or description).strip()
                url = article.get("url", "")
                source = article.get("source", {}).get("name", "NewsAPI")
                author = article.get("author") or source
                published_at = article.get("publishedAt", "")
                image_url = article.get("urlToImage") or "N/A"

                if not title or not url:
                    continue

                # Remove "[+N chars]" truncation marker NewsAPI appends
                if content and "[+" in content:
                    content = content[:content.rfind("[+")].strip()

                # Parse ISO 8601 date
                date_str = "N/A"
                try:
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%B %d, %Y")
                except Exception:
                    pass

                if self.spam_content_check(title + " " + description):
                    continue

                body = content if content else description
                news_data.append({
                    "id": self.sorting.ordering_date(date_str) if date_str != "N/A" else 0,
                    "headlines": title,
                    "author": author,
                    "fullNews": body[:500] + "..." if len(body) > 500 else body,
                    "newsURL": url,
                    "newsImgURL": image_url,
                    "newsDate": date_str
                })

        except Exception as e:
            print(f"[NewsAPI Connector] Extraction failed: {e}")

        # Deduplicate
        seen = set()
        unique = [item for item in news_data if not (item["newsURL"] in seen or seen.add(item["newsURL"]))]
        return self.sorting.ordering_news(unique)
