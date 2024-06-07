from flask import *
from controllers.NewsController import NewsController

routes = Blueprint("routes", __name__)
news_controller = NewsController()

"""
home page route
"""
@routes.route("/", methods=["GET"])
def home_route():
    return render_template("home.html")

"""
return news without considering keywords
"""

@routes.route("/news", methods=["GET"])
def getNews_route():
    news = news_controller.getNews()
    print(news)
    return render_template("news.html", data=news)


"""
return news based on certain keywords
"""


@routes.route("/news_keywords", methods=["GET"])
def getNewsWithKeywords_route():
    # get list of keywords as argument from User's request
    user_keywords = request.args.getlist("keywords")
    data = news_controller.getNewsWithKeywords(user_keywords[0])
    print(data)
    return render_template("news_key.html", data=data,keywaord=user_keywords[0])


"""
deal requests with wrong route
"""


@routes.errorhandler(404)
def notFound_route(error):
    news_controller.notFound(error)
