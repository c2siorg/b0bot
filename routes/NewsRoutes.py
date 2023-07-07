from flask import *
from controllers.NewsController import *

routes = Blueprint("routes", __name__)

"""
return news without considering keywords
"""


@routes.route("/news", methods=["GET"])
def getNews_route():
    return getNews()


"""
return news based on certain keywords
"""


@routes.route("/news_keywords", methods=["GET"])
def getNewsWithKeywords_route():
    # get list of keywords as argument from User's request
    user_keywords = request.args.getlist("keywords")
    return getNewsWithKeywords(user_keywords)


"""
deal requests with wrong route
"""


@routes.errorhandler(404)
def notFound_route(error):
    notFound(error)
