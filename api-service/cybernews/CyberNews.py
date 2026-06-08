import json
import os
from cybernews.extractor import Extractor
from cybernews.social_connectors.rss_extractor import RSSExtractor
from cybernews.social_connectors.youtube_connector import YouTubeConnector
from cybernews.social_connectors.newsapi_connector import NewsAPIConnector

class CyberNews:
    def __init__(self) -> None:
        self._extractor = Extractor()
        self._rss_extractor = RSSExtractor()
        self._youtube_connector = YouTubeConnector()
        self._newsapi_connector = NewsAPIConnector()
        
        self._news_types = self.load_json_config('cybernews/news_types.json')
        self._social_sources = {}
        if os.path.exists('cybernews/social_sources.json'):
            self._social_sources = self.load_json_config('cybernews/social_sources.json')

    def load_json_config(self, json_file):
        with open(json_file, 'r', encoding='utf-8') as file:
            return json.load(file)

    @property
    def get_news_types(self) -> list:
        return [news_type for news in self._news_types for news_type, _ in news.items()]

    def get_news(self, news) -> list:
        combined_news = []
        
        # 1. Fetch from standard web extractors
        for news_type in self._news_types:
            if news in news_type:
                try:
                    combined_news.extend(self._extractor.data_extractor(news_type[news]))
                except Exception as e:
                    print(f"Web extraction error for '{news}': {e}")
                    
        # 2. Fetch from Social Extractors (only on relevant cybersecurity topics)
        if news in ['general', 'cyberAttack', 'dataBreach', 'vulnerability', 'security', 'malware']:
            # Get the category-specific query for API connectors
            api_query = self._social_sources.get("api_queries", {}).get(news)
            try:
                # Layer 1: Free RSS feeds (Reddit, Krebs, BleepingComputer, CISA, etc.)
                if "rss" in self._social_sources and "feeds" in self._social_sources["rss"]:
                    rss_data = self._rss_extractor.process_feeds(self._social_sources["rss"]["feeds"])
                    print(f"[{news}] RSS feeds → {len(rss_data)} articles")
                    combined_news.extend(rss_data)

                # Layer 2: Optional YouTube Data API v3 (requires YOUTUBE_API_KEY)
                youtube_data = self._youtube_connector.extract(query=api_query)
                if youtube_data:
                    print(f"[{news}] YouTube API → {len(youtube_data)} videos (query: '{api_query}')")
                combined_news.extend(youtube_data)

                # Layer 2: Optional NewsAPI.org (requires NEWSAPI_KEY)
                newsapi_data = self._newsapi_connector.extract(query=api_query)
                if newsapi_data:
                    print(f"[{news}] NewsAPI → {len(newsapi_data)} articles (query: '{api_query}')")
                combined_news.extend(newsapi_data)

            except Exception as e:
                print(f"Social extraction error: {e}")

        if not combined_news:
            raise ValueError(f"News type '{news}' not found or yielded zero results")
            
        # Re-sort the combined list to interleave social news with web news chronologically
        try:
            from cybernews.sorting import Sorting
            sorter = Sorting()
            return sorter.ordering_news(combined_news)
        except Exception:
            return combined_news
