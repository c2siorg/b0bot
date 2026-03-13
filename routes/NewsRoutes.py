from flask import Blueprint, g, jsonify, render_template, request
from controllers.NewsController import NewsController

routes = Blueprint("routes", __name__)
news_controller = None


def _build_controller(llm_name):
    try:
        return NewsController(llm_name)
    except ValueError:
        return None


def _default_controller():
    global news_controller
    if news_controller is None:
        news_controller = NewsController("mistralai")
    return news_controller


def _invalid_model_response(llm_name):
    return (
        jsonify(
            {
                "error": f"Unsupported llm_name: {llm_name}",
                "supported_models": ["llama", "gemma", "mistralai"],
            }
        ),
        400,
    )


def _extract_keyword():
    user_keywords = [keyword.strip() for keyword in request.args.getlist("keywords")]
    user_keywords = [keyword for keyword in user_keywords if keyword]
    return user_keywords[0] if user_keywords else None

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
    g.news_controller = _build_controller(llm_name)
    if g.news_controller is None:
        return _invalid_model_response(llm_name)
    return render_template("llm.html", llm_name=llm_name)


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    g.news_controller = _build_controller(llm_name)
    if g.news_controller is None:
        return _invalid_model_response(llm_name)
    news = g.news_controller.getNews()
    return render_template("news.html", data=news)


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    g.news_controller = _build_controller(llm_name)
    if g.news_controller is None:
        return _invalid_model_response(llm_name)

    keyword = _extract_keyword()
    if not keyword:
        return jsonify({"error": "Missing required query parameter: keywords"}), 400

    data = g.news_controller.getNewsWithKeywords(keyword)
    return render_template("news_key.html", data=data, keyword=keyword)


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    controller = getattr(g, "news_controller", None)
    if controller is None:
        try:
            controller = _default_controller()
        except Exception:
            return jsonify({"error": "Route not found"}), 404
    return controller.notFound(error)
