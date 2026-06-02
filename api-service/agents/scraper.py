from agents.state import PlannerState
from models.NewsModel import CybernewsDB

db = CybernewsDB()

def scraper_agent(state: PlannerState) -> PlannerState:
    keywords = state.get("keywords", [])
    intent = state.get("intent", "search")

    if keywords and intent == "search":
        keyword_str = " ".join(keywords)
        articles = db.get_news_collections(is_keyword=True, keyword=keyword_str)
    else:
        articles = db.get_news_collections()

    # Normalize to standard format
    normalized = [
        {
            "title": a.get("headlines", "No title"),
            "source": a.get("author", "No source"),
            "date": a.get("newsDate", "No date"),
            "url": a.get("newsURL", "No URL"),
            "body": a.get("fullNews", ""),
        }
        for a in articles[:10]
    ]

    return {**state, "retrieved_articles": normalized}
