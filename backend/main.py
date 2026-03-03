"""
B0Bot – CyberSecurity News API (FastAPI)

Entry-point that wires up middleware, exception handlers, routers,
and shared application state via the ASGI lifespan protocol.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.repositories.news_repository import NewsRepository
from app.routers import news as news_router
from app.services.news_service import NewsService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialise expensive, shared resources once at startup and
    store them on ``app.state`` so they can be injected via Depends().
    """
    settings = get_settings()

    repository = NewsRepository(settings)
    service = NewsService(repository=repository, settings=settings)

    app.state.news_service = service

    yield  # ── application is running ──

    # Cleanup hooks (if needed in future phases)


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

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TODO: lock down for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ───────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(news_router.router, prefix="/api/v1", tags=["News"])


# ── Root / Health ─────────────────────────────────────────────────────────────
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


# ── Direct execution ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)