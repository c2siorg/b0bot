from fastapi import Depends, HTTPException, Request

from app.services.news_service import NewsService


def get_news_service(request: Request) -> NewsService:
    """Pull the NewsService that was created during lifespan startup."""
    service = getattr(request.app.state, "news_service", None)
    if service is None:
        raise HTTPException(
            status_code=500,
            detail="Internal configuration error: NewsService not initialised.",
        )
    return service