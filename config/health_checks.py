import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values


REQUIRED_ENV_VARS = ["HUGGINGFACE_TOKEN", "PINECONE_API_KEY"]
REQUIRED_MODELS = ["llama", "gemma", "mistralai"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_environment(env_path: str = ".env") -> dict:
    env_vars = dotenv_values(env_path)
    missing = [name for name in REQUIRED_ENV_VARS if not env_vars.get(name)]
    return {
        "ok": len(missing) == 0,
        "missing": missing,
    }


def validate_llm_config(llm_config_path: str = "config/llm_config.json") -> dict:
    config_file = Path(llm_config_path)
    if not config_file.exists():
        return {
            "ok": False,
            "errors": [f"Missing config file: {llm_config_path}"],
            "models": [],
        }

    try:
        with config_file.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "errors": [f"Invalid JSON in {llm_config_path}: {exc}"],
            "models": [],
        }

    missing_models = [
        model_name
        for model_name in REQUIRED_MODELS
        if not isinstance(config.get(model_name), str) or not config.get(model_name).strip()
    ]

    errors = []
    if missing_models:
        errors.append(
            "Missing model mapping(s): " + ", ".join(sorted(missing_models))
        )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "models": sorted(config.keys()),
    }


def validate_pinecone_connection() -> dict:
    try:
        from config.Database import client

        indexes = client.list_indexes()
        index_names = []

        if hasattr(indexes, "names") and callable(indexes.names):
            index_names = indexes.names()
        elif isinstance(indexes, list):
            index_names = indexes

        return {
            "ok": True,
            "indexes": index_names,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "indexes": [],
            "error": str(exc),
        }


def get_health_payload() -> dict:
    return {
        "status": "ok",
        "service": "b0bot",
        "timestamp": _utc_now_iso(),
    }


def get_readiness_payload() -> dict:
    env_check = validate_environment()
    llm_check = validate_llm_config()
    pinecone_check = validate_pinecone_connection()

    checks = {
        "environment": env_check,
        "llm_config": llm_check,
        "pinecone": pinecone_check,
    }

    errors = []
    if not env_check["ok"]:
        errors.append("Missing required environment variables")
    if not llm_check["ok"]:
        errors.extend(llm_check["errors"])
    if not pinecone_check["ok"]:
        errors.append("Pinecone connectivity check failed")

    return {
        "status": "ready" if not errors else "not-ready",
        "timestamp": _utc_now_iso(),
        "checks": checks,
        "errors": errors,
    }
