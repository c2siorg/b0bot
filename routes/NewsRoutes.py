from flask import *
from controllers.NewsController import NewsController
from config.health_checks import get_health_payload, get_readiness_payload

routes = Blueprint("routes", __name__)
news_controller = NewsController("mistralai") # default model name

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
    # get list of keywords as argument from User's request
    g.news_controller = NewsController(llm_name)
    user_keywords = request.args.getlist("keywords")
    data = g.news_controller.getNewsWithKeywords(user_keywords[0])
    return render_template("news_key.html", data=data,keyword=user_keywords[0])


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    return jsonify({"error": "Not Found", "detail": str(error)}), 404
