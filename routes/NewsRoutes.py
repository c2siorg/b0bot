from flask import *
from controllers.NewsController import NewsController
routes = Blueprint("routes", __name__)
news_controller = NewsController("qwen") # default model name

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
    g.news_controller = NewsController(llm_name)
    return render_template("llm.html", llm_name=llm_name)


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    g.news_controller = NewsController(llm_name)
    news = g.news_controller.getNews()
    return render_template("news.html", data=news)


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    # Get keywords and reject empty/whitespace-only input.
    user_keywords = request.args.get("keywords", "").strip()
    if not user_keywords:
        return render_template(
            "llm.html",
            llm_name=llm_name,
            keyword_error="Please enter at least one keyword before submitting.",
        ), 400

    g.news_controller = NewsController(llm_name)
    data = g.news_controller.getNewsWithKeywords(user_keywords)
    return render_template("news_key.html", data=data, keyword=user_keywords)


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    g.news_controller.notFound(error)
