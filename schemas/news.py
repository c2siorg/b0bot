from typing import Optional

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    title: str = Field(
        ...,
        description="Headline / title of the news article",
        examples=["Critical Apache vulnerability patched"],
    )
    source: str = Field(
        ...,
        description="Publisher or news source",
        examples=["The Hacker News"],
    )
    date: str = Field(
        ...,
        description="Publication date (DD/MM/YYYY or as provided by the LLM)",
        examples=["15/06/2024"],
    )
    url: str = Field(
        ...,
        description="URL to the full article",
        examples=["https://thehackernews.com/2024/06/example.html"],
    )


class NewsResponse(BaseModel):
    llm: str = Field(
        ...,
        description="Name of the LLM model that processed the news",
        examples=["llama"],
    )
    keywords: Optional[str] = Field(
        None,
        description="Keywords that were used to filter the news (if any)",
    )
    count: int = Field(
        ...,
        description="Number of news items in this response",
    )
    news: list[NewsItem] = Field(
        default_factory=list,
        description="Ordered list of processed news articles",
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="Human-readable error message",
    )


class ModelsResponse(BaseModel):
    available_models: list[str] = Field(
        ...,
        description="Model short-names accepted by the /{llm_name}/ routes",
    )
