import os
from datetime import datetime
from cybernews.performance import Performance
from cybernews.sorting import Sorting

# NOTE: Requires YOUTUBE_API_KEY in your .env
# Get a free key (10,000 units/day) at: https://console.cloud.google.com
# Enable "YouTube Data API v3" in your Google Cloud project.

class YouTubeConnector(Performance):
    """
    Optional connector that uses the official YouTube Data API v3 to search
    for recent cybersecurity-related videos.

    Activation: Set YOUTUBE_API_KEY in your .env file.
    If the key is absent, this connector silently skips and returns an empty list.
    """

    FALLBACK_QUERY = "cybersecurity OR infosec OR CVE"
    MAX_RESULTS = 15

    def __init__(self):
        super().__init__()
        self.sorting = Sorting()
        self.is_configured = False
        self._youtube = None

        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            print("[YouTube Connector] Skipping: YOUTUBE_API_KEY not found in env.")
            return

        try:
            from googleapiclient.discovery import build
            self._youtube = build("youtube", "v3", developerKey=api_key)
            self.is_configured = True
            print("[YouTube Connector] Initialized successfully.")
        except ImportError:
            print("[YouTube Connector] Skipping: 'google-api-python-client' not installed. Run: pip install google-api-python-client")
        except Exception as e:
            print(f"[YouTube Connector] Initialization failed: {e}")

    def extract(self, query: str = None) -> list:
        """
        Searches YouTube for recent cybersecurity videos.
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
            request = self._youtube.search().list(
                part="snippet",
                q=search_query,
                type="video",
                order="date",
                maxResults=self.MAX_RESULTS,
                relevanceLanguage="en"
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")
                if not video_id:
                    continue

                title = snippet.get("title", "").strip()
                description = snippet.get("description", "").strip()
                channel = snippet.get("channelTitle", "N/A")
                published_at = snippet.get("publishedAt", "")
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                # Parse ISO 8601 date
                date_str = "N/A"
                try:
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%B %d, %Y")
                except Exception:
                    pass

                if not title or self.spam_content_check(title + " " + description):
                    continue

                news_data.append({
                    "id": self.sorting.ordering_date(date_str) if date_str != "N/A" else 0,
                    "headlines": f"[YouTube] {title}",
                    "author": channel,
                    "fullNews": description[:500] + "..." if len(description) > 500 else description,
                    "newsURL": video_url,
                    "newsImgURL": snippet.get("thumbnails", {}).get("high", {}).get("url", "N/A"),
                    "newsDate": date_str
                })

        except Exception as e:
            print(f"[YouTube Connector] Extraction failed: {e}")

        # Deduplicate
        seen = set()
        unique = [item for item in news_data if not (item["newsURL"] in seen or seen.add(item["newsURL"]))]
        return self.sorting.ordering_news(unique)
