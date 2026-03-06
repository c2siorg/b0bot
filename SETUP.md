# Setup Guide

This guide will walk you through the steps to set up and run the B0Bot CyberSecurity News API.

## Prerequisites

- **Python**: Version 3.10 or higher.
- **uv**: A fast Python package installer and resolver. [Install uv](https://github.com/astral-sh/uv).

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd b0bot
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and add your API tokens:

```env
# HuggingFace (Used for LLM processing)
HUGGINGFACE_TOKEN=your_huggingface_token

# Pinecone (Used for the knowledge base)
PINECONE_API_KEY=your_pinecone_api_key
```

### 3. Install Dependencies

Use `uv` to create a virtual environment and install all necessary packages as defined in `pyproject.toml`:

```bash
uv sync
```

### 4. Initialize the Knowledge Base

Before running the API, you need to populate the Pinecone index with the latest cybersecurity news. Run the update script:

```bash
uv run db_update/Update.py
```

*Note: This will scrape news, generate embeddings, and upsert them to Pinecone.*

### 5. Run the Application

Start the FastAPI server using `uv`:

```bash
uv run uvicorn main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Once the server is running, you can access the interactive Swagger UI at:
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Key Endpoints

- `GET /health`: Check server status.
- `GET /api/v1/models`: List available LLM models.
- `GET /api/v1/{llm_name}/news`: Get summarized news using a specific model.
- `GET /api/v1/{llm_name}/news_keywords`: Get news filtered by keywords.

## Project Structure

- `main.py`: Entry point for the FastAPI application.
- `app_config.py`: Configuration settings using Pydantic.
- `cybernews/`: Core logic for scraping and extracting news.
- `db_update/`: Scripts for updating the Pinecone index.
- `services/`: News processing and LLM integration logic.
- `repositories/`: Database abstraction layer (Pinecone).
- `routers/`: API route definitions.
- `schemas/`: Pydantic models for request/response validation.
- `config/`: Configuration files (e.g., `llm_config.json`).
- `prompts/`: LLM prompt templates.
