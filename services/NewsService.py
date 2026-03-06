from services.AgentTools import fetch_cyber_news

class NewsService:
    @staticmethod
    def get_consolidated_news(categories):
        """
        Logic to fetch from multiple sources and remove duplicates.
        """
        all_news = []
        seen_titles = set()

        # Ensure categories is a list
        if isinstance(categories, str):
            categories = [categories]

        for cat in categories:
            # We assume fetch_cyber_news is a LangChain runnable/mock
            try:
                raw_data = fetch_cyber_news.invoke(cat)
                for item in raw_data:
                    title = item.get("title", "").lower()
                    if title and title not in seen_titles and len(title) > 10:
                        all_news.append(item)
                        seen_titles.add(title)
            except Exception as e:
                print(f"Error fetching for category {cat}: {e}")
        
        return all_news

    @staticmethod
    def db_update_status():
        return {"status": "synchronized", "last_update": "Just now"}