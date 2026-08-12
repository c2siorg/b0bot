from flask import *
from controllers.NewsController import NewsController
from models.SubscriberModel import SubscriberDB
from agents.notification import KNOWN_INTEREST_TAGS
import json
import os
import redis

routes = Blueprint("routes", __name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL = int(os.getenv("SESSION_TTL", "3600"))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "10"))

try:
    session_store = redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    session_store = None

def _session_key(session_id: str) -> str:
    return f"session:{session_id}:history"

def _load_history(session_id: str) -> list:
    if not session_store:
        return []
    try:
        raw = session_store.get(_session_key(session_id))
        return json.loads(raw) if raw else []
    except Exception:
        return []

def _save_history(session_id: str, history: list):
    if not session_store:
        return
    try:
        session_store.setex(_session_key(session_id), SESSION_TTL, json.dumps(history))
    except Exception:
        pass

"""
home page route
"""
@routes.route("/", methods=["GET"])
def home_route():
    return render_template("landing.html")

"""
set route for different LLM models
"""
@routes.route("/<llm_name>", methods=["GET"])
def set_llm_route(llm_name):
    if llm_name == "favicon.ico":
        return "", 204
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
    g.news_controller = NewsController(llm_name)
    user_keywords = request.args.getlist("keywords")
    data = g.news_controller.getNewsWithKeywords(user_keywords[0])
    return render_template("news_key.html", data=data, keyword=user_keywords[0])

"""
return news without considering keywords (NO LLM)
"""
@routes.route("/raw/news", methods=["GET"])
def getNews_raw_route():
    g.news_controller = NewsController(None)
    news = g.news_controller.getNews()
    return render_template("news.html", data=news, llm_name="raw")

"""
return news based on certain keywords (NO LLM)
"""
@routes.route("/raw/news_keywords", methods=["GET"])
def getNewsWithKeywords_raw_route():
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
chat UI route
"""
@routes.route("/chat", methods=["GET"])
def chat_ui_route():
    return render_template("chat.html", active_page="chat")

"""
dashboard placeholder route, real dashboard lands week 9
"""
@routes.route("/dashboard", methods=["GET"])
def dashboard_route():
    return render_template("coming_soon.html", active_page="home", page_name="Home")

"""
sources placeholder route, real sources page lands week 9
"""
@routes.route("/sources", methods=["GET"])
def sources_route():
    return render_template("coming_soon.html", active_page="sources", page_name="Sources")

"""
chat route - multi-turn dialogue via LangGraph agents
"""
@routes.route("/chat", methods=["POST"])
def chat_route():
    data = request.get_json()
    user_input = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not user_input:
        return jsonify({"error": "message is required"}), 400

    history = _load_history(session_id)

    from agents import agent_graph
    result = agent_graph.invoke({
        "user_input": user_input,
        "session_id": session_id,
        "chat_history": history,
        "notification_triggered": False,
    })

    response = result["llm_response"]

    history.append({"role": "user", "content": user_input, "intent": result.get("intent")})
    history.append({"role": "assistant", "content": response})
    _save_history(session_id, history[-MAX_HISTORY:])

    return jsonify({"response": response}), 200

"""
subscribe form - GET renders the form, POST creates the subscriber row
"""
db = SubscriberDB()


@routes.route("/subscribe", methods=["GET"])
def subscribe_form_route():
    prefill_email = request.args.get("email", "")
    return render_template("subscribe.html", interest_tags=sorted(KNOWN_INTEREST_TAGS), active_page="subscribe", prefill_email=prefill_email)


@routes.route("/subscribe", methods=["POST"])
def subscribe_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "invalid request"}), 400

    email = (data.get("email") or "").strip()
    frequency = data.get("frequency") or "daily"
    interests = data.get("interests") or []

    if not email:
        return jsonify({"success": False, "message": "email is required"}), 400
    if frequency not in ("daily", "weekly"):
        return jsonify({"success": False, "message": "frequency must be daily or weekly"}), 400

    valid_interests = [tag for tag in interests if tag in KNOWN_INTEREST_TAGS]

    created = db.create_subscriber(email=email, frequency=frequency, interests=valid_interests)
    if not created:
        return jsonify({"success": False, "message": "something went wrong saving your subscription, please try again"}), 500

    return jsonify({"success": True, "message": "subscribed, you'll get digests based on your interests"}), 200


"""
unsubscribe route - sets status to unsubscribed
"""
@routes.route("/unsubscribe/<subscriber_id>", methods=["GET"])
def unsubscribe_route(subscriber_id):
    success = db.unsubscribe(subscriber_id)
    return render_template("unsubscribe.html", success=success)
