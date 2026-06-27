from flask import Blueprint, render_template, request, g, jsonify
from controllers.NewsController import NewsController

routes = Blueprint("routes", __name__)


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
    try:
        if not llm_name or llm_name == "favicon.ico":
            return "", 204

        g.news_controller = NewsController(llm_name)
        return render_template("llm.html", llm_name=llm_name)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


"""
return news without considering keywords
"""
@routes.route("/<llm_name>/news", methods=["GET"])
def getNews_route(llm_name):
    try:
        if not llm_name:
            return jsonify({"error": "LLM name is required"}), 400

        g.news_controller = NewsController(llm_name)
        news = g.news_controller.getNews()

        if not news:
            return jsonify({"message": "No news found"}), 404

        return render_template("news.html", data=news)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


"""
return news based on certain keywords
"""
@routes.route("/<llm_name>/news_keywords", methods=["GET"])
def getNewsWithKeywords_route(llm_name):
    try:
        if not llm_name:
            return jsonify({"error": "LLM name is required"}), 400

        user_keywords = request.args.getlist("keywords")

        if not user_keywords or not user_keywords[0].strip():
            return jsonify({"error": "Keyword is required"}), 400

        g.news_controller = NewsController(llm_name)
        data = g.news_controller.getNewsWithKeywords(user_keywords[0])

        if not data:
            return jsonify({"message": "No results found"}), 404

        return render_template(
            "news_key.html",
            data=data,
            keyword=user_keywords[0]
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


"""
return news without considering keywords (NO LLM)
"""
@routes.route("/raw/news", methods=["GET"])
def getNews_raw_route():
    try:
        g.news_controller = NewsController(None)
        news = g.news_controller.getNews()

        if not news:
            return jsonify({"message": "No news found"}), 404

        return render_template("news.html", data=news, llm_name="raw")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


"""
return news based on certain keywords (NO LLM)
"""
@routes.route("/raw/news_keywords", methods=["GET"])
def getNewsWithKeywords_raw_route():
    try:
        user_keywords = request.args.getlist("keywords")

        if not user_keywords or not user_keywords[0].strip():
            return jsonify({"error": "Keyword is required"}), 400

        g.news_controller = NewsController(None)
        data = g.news_controller.getNewsWithKeywords(user_keywords[0])

        if not data:
            return jsonify({"message": "No results found"}), 404

        return render_template(
            "news_key.html",
            data=data,
            keyword=user_keywords[0],
            llm_name="raw"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


"""
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    return jsonify({"error": "Route not found"}), 404
