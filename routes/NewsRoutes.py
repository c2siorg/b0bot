from flask import *
from controllers.NewsController import NewsController
import json

routes = Blueprint("routes", __name__)

with open('config/llm_config.json') as f:
    VALID_LLMS = set(json.load(f).keys())

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
        return "", 204
    if llm_name not in VALID_LLMS:
        return jsonify({"error": f"Unsupported model '{llm_name}'. Valid options: {', '.join(VALID_LLMS)}"}), 400
    g.news_controller = NewsController(llm_name)
    return render_template("llm.html", llm_name=llm_name)


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    if llm_name not in VALID_LLMS:
        return jsonify({"error": f"Unsupported model '{llm_name}'. Valid options: {', '.join(VALID_LLMS)}"}), 400
    g.news_controller = NewsController(llm_name)
    news = g.news_controller.getNews()
    return render_template("news.html", data=news)


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    if llm_name not in VALID_LLMS:
        return jsonify({"error": f"Unsupported model '{llm_name}'. Valid options: {', '.join(VALID_LLMS)}"}), 400
    user_keywords = request.args.getlist("keywords")
    if not user_keywords or not user_keywords[0].strip():
        return jsonify({"error": "Keywords parameter is required"}), 400
    g.news_controller = NewsController(llm_name)
    data = g.news_controller.getNewsWithKeywords(user_keywords[0].strip())
    return render_template("news_key.html", data=data, keyword=user_keywords[0])


"""
return news without considering keywords (NO LLM)
"""
@routes.route("/raw/news", methods=["GET"])
def getNews_raw_route():
    g.news_controller = NewsController(None)
    news = g.news_controller.getNews()
    return render_template("news.html", data=news, llm_name="raw")


"""
return news based on certain keywords (NO LLM)
"""
@routes.route("/raw/news_keywords", methods=["GET"])
def getNewsWithKeywords_raw_route():
    user_keywords = request.args.getlist("keywords")
    if not user_keywords or not user_keywords[0].strip():
        return jsonify({"error": "Keywords parameter is required"}), 400
    g.news_controller = NewsController(None)
    data = g.news_controller.getNewsWithKeywords(user_keywords[0].strip())
    return render_template("news_key.html", data=data, keyword=user_keywords[0], llm_name="raw")


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    if hasattr(g, 'news_controller') and g.news_controller is not None:
        return g.news_controller.notFound(error)
    default_controller = NewsController("mistralai")
    return default_controller.notFound(error)
