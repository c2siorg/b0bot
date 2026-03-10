from flask import *
from controllers.NewsController import NewsController
from config.health_checks import get_health_payload, get_readiness_payload
import json


def _load_supported_models(config_path="config/llm_config.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        return set(config.keys())
    except (OSError, json.JSONDecodeError):
        # Fallback keeps routes usable even if config is temporarily unavailable.
        return {"mistralai", "gemma", "llama"}


SUPPORTED_MODELS = _load_supported_models()

routes = Blueprint("routes", __name__)


def _validate_llm_name(llm_name):
    return llm_name in SUPPORTED_MODELS

"""
home page route
"""
@routes.route("/", methods=["GET"])
def home_route():
    return render_template("home.html")


"""
basic liveness endpoint for uptime probes
"""
@routes.route("/health", methods=["GET"])
def health_route():
    return jsonify(get_health_payload()), 200


"""
readiness endpoint checks env/config/external dependencies
"""
@routes.route("/ready", methods=["GET"])
def readiness_route():
    readiness = get_readiness_payload()
    status_code = 200 if readiness["status"] == "ready" else 503
    return jsonify(readiness), status_code


"""
set route for different LLM models
"""
@routes.route("/<llm_name>", methods=["GET"])
def set_llm_route(llm_name):
    if llm_name == "favicon.ico":
        return "", 204  # No Content response for favicon requests

    if not _validate_llm_name(llm_name):
        return (
            render_template(
                "llm.html",
                llm_name=llm_name,
                error_message=(
                    f"Unsupported model '{llm_name}'. "
                    f"Supported models: {', '.join(sorted(SUPPORTED_MODELS))}."
                ),
            ),
            404,
        )

    return render_template("llm.html", llm_name=llm_name)


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    if not _validate_llm_name(llm_name):
        return jsonify({"error": f"Unsupported model: {llm_name}"}), 404

    controller = NewsController(llm_name)
    try:
        news = controller.getNews()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return render_template("news.html", data=news)


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    if not _validate_llm_name(llm_name):
        return jsonify({"error": f"Unsupported model: {llm_name}"}), 404

    # get list of keywords as argument from User's request
    user_keywords = request.args.getlist("keywords")

    if not user_keywords or not user_keywords[0].strip():
        message = "Please provide a non-empty 'keywords' query parameter."
        return (
            render_template("llm.html", llm_name=llm_name, error_message=message),
            400,
        )

    keyword = user_keywords[0].strip()
    controller = NewsController(llm_name)
    try:
        data = controller.getNewsWithKeywords(keyword)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return render_template("news_key.html", data=data, keyword=keyword)


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    return jsonify({"error": "Not Found", "detail": str(error)}), 404
