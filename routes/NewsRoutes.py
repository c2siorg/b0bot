from flask import *
from controllers.NewsController import NewsController
routes = Blueprint("routes", __name__)
news_controller = NewsController("mistralai") # default model name

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
    print("ROUTE RECEIVED DATA:", news) 
    return render_template("news.html", data=news)


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    g.news_controller = NewsController(llm_name)

    user_keywords = request.args.get("keywords")

    if not user_keywords or not user_keywords.strip():
        flash("Please enter a keyword before searching.")
        return redirect(url_for("routes.set_llm_route", llm_name=llm_name))

    cleaned_keyword = user_keywords.strip()
    data = g.news_controller.getNewsWithKeywords(cleaned_keyword)

    return render_template("news_key.html", data=data, keyword=cleaned_keyword)

"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    g.news_controller.notFound(error)
