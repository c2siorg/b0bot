from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_config import get_settings
from exceptions import register_exception_handlers
from repositories.news_repository import NewsRepository
from routers import news as news_router
from services.news_service import NewsService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    repository = NewsRepository(settings)
    service = NewsService(repository=repository, settings=settings)

    app.state.news_service = service

    yield 



app = FastAPI(
    title="B0Bot – CyberSecurity News API",
    description=(
        "A REST API that retrieves the latest cybersecurity news from a "
        "Pinecone knowledge-base, processes it through selectable HuggingFace "
        "LLMs (Llama-3, Gemma, MistralAI), and returns structured JSON."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(news_router.router, prefix="/api/v1", tags=["News"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to B0Bot – CyberSecurity News API",
        "docs": "/docs",
        "available_llms": ["llama", "gemma", "mistralai"],
        "endpoints": {
            "news": "/api/v1/{llm_name}/news",
            "news_keywords": "/api/v1/{llm_name}/news_keywords?keywords=<keyword>",
            "models": "/api/v1/models",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)