from flask import *
from controllers.NewsController import NewsController
routes = Blueprint("routes", __name__)
from werkzeug.exceptions import HTTPException
# news_controller = NewsController("mistralai") # default model name

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
    # get list of keywords as argument from User's request
    g.news_controller = NewsController(llm_name)
    user_keywords = request.args.getlist("keywords")
    data = g.news_controller.getNewsWithKeywords(user_keywords[0])
    return render_template("news_key.html", data=data, keyword=user_keywords[0])


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
    # Instantiate without a model to bypass LLM initialization entirely
    g.news_controller = NewsController(None)
    user_keywords = request.args.getlist("keywords")
    data = g.news_controller.getNewsWithKeywords(user_keywords[0])
    return render_template("news_key.html", data=data, keyword=user_keywords[0], llm_name="raw")


"""
deal requests with wrong route
"""
@routes.errorhandler(Exception)
def handle_all_errors(error):
    """
    Generic error handler for all exceptions
    """

    # Default values
    status_code = 500
    error_name = "Internal Server Error"
    error_description = "Something went wrong."

    # If it's an HTTPException (like 404, 400, etc.)
    if isinstance(error, HTTPException):
        status_code = error.code
        error_name = error.name
        error_description = error.description

    # Log error (important for debugging)
    print(f"[ERROR] {error_name} ({status_code}): {error}")

    # Return HTML page
    return render_template(
        "error.html",
        status_code=status_code,
        error_name=error_name,
        error_description=error_description
    ), status_code