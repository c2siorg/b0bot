from flask import *
from controllers.NewsController import NewsController
import logging

logger = logging.getLogger(__name__)
routes = Blueprint("routes", __name__)

# Initialize default controller with error handling
try:
    news_controller = NewsController("mistralai")  # default model name
    logger.info("✓ Default news controller initialized")
except Exception as e:
    logger.error(f"⚠ Failed to initialize default news controller: {e}")
    news_controller = None

"""
home page route
"""
@routes.route("/", methods=["GET"])
def home_route():
    return render_template("home.html")


"""
set route for different LLM models
"""
@routes.route("/<llm_name>", methods=["GET"])
def set_llm_route(llm_name):
    if llm_name == "favicon.ico":
        return "", 204  # No Content response for favicon requests
    try:
        g.news_controller = NewsController(llm_name)
        return render_template("llm.html", llm_name=llm_name)
    except Exception as e:
        logger.error(f"Error initializing controller for {llm_name}: {e}")
        return render_template("llm.html", llm_name=llm_name, error=str(e))


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    try:
        g.news_controller = NewsController(llm_name)
        news = g.news_controller.getNews()
        return render_template("news.html", data=news)
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        return render_template("news.html", data=[], error=str(e))


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    try:
        g.news_controller = NewsController(llm_name)
        user_keywords = request.args.getlist("keywords")
        if not user_keywords:
            return render_template("news_key.html", data=[], keyword="", error="No keywords provided")
        data = g.news_controller.getNewsWithKeywords(user_keywords[0])
        return render_template("news_key.html", data=data, keyword=user_keywords[0])
    except Exception as e:
        logger.error(f"Error getting news with keywords: {e}")
        return render_template("news_key.html", data=[], keyword="", error=str(e))


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    logger.warning(f"404 Not found: {error}")
    if news_controller:
        news_controller.notFound(error)
    return render_template("error.html", error="Page not found"), 404
