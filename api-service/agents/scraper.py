from agents.state import PlannerState
from models.NewsModel import CybernewsDB
from services.embeddings import generate_embedding

db = CybernewsDB()

# Generic words that don't narrow down a search
GENERIC_TERMS = {"cybersecurity", "news", "security", "latest", "cyber", "articles", "show", "me"}

def scraper_agent(state: PlannerState) -> PlannerState:
    keywords = state.get("keywords", [])
    intent = state.get("intent", "search")
    user_input = state.get("user_input", "")

    # Filter out generic terms to get meaningful keywords
    meaningful_keywords = [k for k in keywords if k.lower() not in GENERIC_TERMS]

    if meaningful_keywords and intent == "search":
        keyword_str = " ".join(meaningful_keywords)
        query_vector = generate_embedding(user_input)
        articles = db.get_news_collections(
            is_keyword=True,
            keyword=keyword_str,
            search_type="hybrid",
            query_vector=query_vector or None,
        )
        # Fall back to all articles if keyword search returns nothing
        if not articles:
            articles = db.get_news_collections()
    else:
        articles = db.get_news_collections()

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
