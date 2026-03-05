import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_news_service        
from app.schemas.news import ErrorResponse, ModelsResponse, NewsResponse
from app.services.news_service import NewsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=ModelsResponse, summary="List available LLM models")
async def list_models(service: NewsService = Depends(get_news_service)):
    return ModelsResponse(available_models=service.available_models)


@router.get(
    "/{llm_name}/news",
    response_model=NewsResponse,
    responses={
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Get summarised cybersecurity news",
)
async def get_general_news(
    llm_name: str,
    service: NewsService = Depends(get_news_service),
):
    return await service.get_news(llm_name=llm_name)


@router.get(
    "/{llm_name}/news_keywords",
    response_model=NewsResponse,
    responses={
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Get keyword-filtered cybersecurity news",
)
async def get_keyword_news(
    llm_name: str,
    keywords: str = Query(..., min_length=2),
    service: NewsService = Depends(get_news_service),
):
    return await service.get_news(llm_name=llm_name, keywords=keywords)