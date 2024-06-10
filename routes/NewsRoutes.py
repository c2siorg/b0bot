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
    g.news_controller = NewsController(llm_name)
    return render_template(f"{llm_name}.html")


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
    user_keywords = request.args.getlist("keywords")
    data = g.news_controller.getNewsWithKeywords(user_keywords[0])
    return render_template("news_key.html", data=data,keyword=user_keywords[0])


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    g.news_controller.notFound(error)
