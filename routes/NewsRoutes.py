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
    try:
        g.news_controller = NewsController(llm_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return render_template("llm.html", llm_name=llm_name)


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    try:
        g.news_controller = NewsController(llm_name)
        news = g.news_controller.getNews()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to retrieve news", "details": str(e)}), 500
    return render_template("news.html", data=news)


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    # get list of keywords as argument from User's request
    user_keywords = request.args.getlist("keywords")
    if not user_keywords or not user_keywords[0].strip():
        return jsonify({"error": "At least one keyword must be provided via ?keywords=<value>"}), 400
    try:
        g.news_controller = NewsController(llm_name)
        data = g.news_controller.getNewsWithKeywords(user_keywords[0])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to retrieve news", "details": str(e)}), 500
    return render_template("news_key.html", data=data, keyword=user_keywords[0])


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    return jsonify({"error": "Route not found", "status": 404}), 404
