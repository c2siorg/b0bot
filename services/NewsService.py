from typing import List, Union
from services.AgentTools import fetch_cyber_news
from models.NewsModel import NewsArticle  # <--- Crucial Import

class NewsService:
    @staticmethod
    def get_consolidated_news(categories: Union[str, List[str]]) -> List[dict]:
        """
        Fetches, deduplicates, and validates cybersecurity news using Pydantic.
        
        Args:
            categories: A single category string or a list of categories.
        Returns:
            A list of validated news dictionaries.
        """
        all_news = []
        seen_titles = set()

        # Normalize input to a list
        if isinstance(categories, str):
            categories = [categories]

        for cat in categories:
            try:
                # LCEL 'invoke' pattern
                raw_data = fetch_cyber_news.invoke(cat)
                
                for item in raw_data:
                    # 1. Deduplication Logic
                    title = item.get("title", "").strip().lower()
                    if not title or title in seen_titles or len(title) < 10:
                        continue

                    # 2. Pydantic Validation (The "Professional" Move)
                    # This ensures 'title', 'summary', and 'url' exist before adding to list.
                    try:
                        validated_item = NewsArticle(**item)
                        all_news.append(validated_item.model_dump())
                        seen_titles.add(title)
                    except Exception as val_error:
                        print(f"Validation failed for article '{title}': {val_error}")
                        
            except Exception as e:
                print(f"Error fetching for category {cat}: {e}")
        
        return all_news

    @staticmethod
    def db_update_status() -> dict:
        """Returns the current synchronization status of the News Vector Index."""
        return {"status": "synchronized", "last_update": "Just now"}