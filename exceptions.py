import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class B0BotError(Exception):
    pass


class LLMNotFoundError(B0BotError):
    def __init__(self, model_name: str, available: list[str]) -> None:
        self.model_name = model_name
        self.available = available
        super().__init__(
            f"LLM '{model_name}' not found. Available models: {available}"
        )


class LLMProcessingError(B0BotError):
    pass


class NewsFetchError(B0BotError):
    pass


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(LLMNotFoundError)
    async def llm_not_found_handler(request: Request, exc: LLMNotFoundError):
        logger.warning(str(exc))
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(LLMProcessingError)
    async def llm_processing_error_handler(request: Request, exc: LLMProcessingError):
        logger.error(f"LLM Processing Error: {exc}")
        return JSONResponse(
            status_code=502,
            content={"detail": "Failed to process news with the underlying LLM."},
        )

    @app.exception_handler(NewsFetchError)
    async def news_fetch_error_handler(request: Request, exc: NewsFetchError):
        logger.error(f"News Fetch Error: {exc}")
        return JSONResponse(
            status_code=503,
            content={"detail": "Failed to retrieve news from the knowledge base."},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred."},
        )