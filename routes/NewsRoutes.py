from flask import *
from controllers.NewsController import NewsController
routes = Blueprint("routes", __name__)

MAX_KEYWORD_LENGTH = 200


def _validate_keyword(raw_list):
    """
    Validates the ?keywords= query parameter.

    Returns (keyword, error_response):
      - On success: (stripped_keyword, None)
      - On failure: (None, (json_response, status_code))

    Checks performed:
      1. Parameter must be present.
      2. Value must be non-empty after stripping whitespace.
      3. Value must not exceed MAX_KEYWORD_LENGTH characters.
    """
    if not raw_list:
        return None, (jsonify({"error": "Missing required query parameter: keywords"}), 400)

    keyword = raw_list[0].strip()

    if not keyword:
        return None, (jsonify({"error": "keywords parameter cannot be empty"}), 400)

    if len(keyword) > MAX_KEYWORD_LENGTH:
        return None, (
            jsonify({
                "error": f"keywords parameter exceeds maximum length of {MAX_KEYWORD_LENGTH} characters"
            }),
            400,
        )

    return keyword, None


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
    keyword, err = _validate_keyword(request.args.getlist("keywords"))
    if err:
        return err

    g.news_controller = NewsController(llm_name)
    data = g.news_controller.getNewsWithKeywords(keyword)
    return render_template("news_key.html", data=data, keyword=keyword)


"""
return news without considering keywords (NO LLM)
"""
@routes.route("/raw/news", methods=["GET"])
def getNews_raw_route():
    # Instantiate without a model to bypass LLM initialization entirely
    g.news_controller = NewsController(None)
    news = g.news_controller.getNews()
    return render_template("news.html", data=news, llm_name="raw")


"""
return news based on certain keywords (NO LLM)
"""
@routes.route("/raw/news_keywords", methods=["GET"])
def getNewsWithKeywords_raw_route():
    keyword, err = _validate_keyword(request.args.getlist("keywords"))
    if err:
        return err

    # Instantiate without a model to bypass LLM initialization entirely
    g.news_controller = NewsController(None)
    data = g.news_controller.getNewsWithKeywords(keyword)
    return render_template("news_key.html", data=data, keyword=keyword, llm_name="raw")


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    g.news_controller.notFound(error)
