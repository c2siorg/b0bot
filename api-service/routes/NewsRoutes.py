from flask import *
from controllers.NewsController import NewsController
routes = Blueprint("routes", __name__)
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
@routes.errorhandler(404)
def notFound_route(error):
    g.news_controller.notFound(error)

"""
health check route
"""
@routes.route("/health", methods=["GET"])
def health_route():
    return jsonify({"status": "ok"}), 200

"""
chat route — multi-turn dialogue via LangGraph agents
"""
@routes.route("/chat", methods=["POST"])
def chat_route():
    data = request.get_json()
    user_input = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not user_input:
        return jsonify({"error": "message is required"}), 400

    from agents import agent_graph
    result = agent_graph.invoke({
        "user_input": user_input,
        "session_id": session_id,
        "chat_history": [],
        "notification_triggered": False,
    })

    return jsonify({"response": result["llm_response"]}), 200

"""
subscribe stub route
"""
@routes.route("/subscribe", methods=["POST"])
def subscribe_route():
    return jsonify({"message": "subscription endpoint — coming soon"}), 200
