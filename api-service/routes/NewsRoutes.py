import json
import os

import redis
from flask import Blueprint, jsonify, render_template, request

from agents.notification import KNOWN_INTEREST_TAGS
from models.NewsModel import CybernewsDB
from models.SourceModel import SourceDB
from models.SubscriberModel import SubscriberDB

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
deal requests with wrong route
"""
@routes.errorhandler(404)
def notFound_route(error):
    return jsonify({"error": "not found"}), 404

"""
health check route
"""
@routes.route("/health", methods=["GET"])
def health_route():
    return jsonify({"status": "ok"}), 200


"""
chat UI route
"""
news_db = CybernewsDB()
@routes.route("/chat", methods=["GET"])
def chat_ui_route():
    article_id = request.args.get("article_id")
    article = news_db.get_article_by_id(article_id) if article_id else None
    return render_template("chat.html", active_page="chat", article=article)

"""
dashboard - shows the feed, top news panel, and cve watchlist
"""
DASHBOARD_FILTERS = {"newest", "critical", "frequent"}
@routes.route("/dashboard", methods=["GET"])
def dashboard_route():
    filter = request.args.get("filter", "newest")
    if filter not in DASHBOARD_FILTERS:
        filter = "newest"
    source = request.args.get("source") or None
    return render_template(
        "dashboard.html",
        active_page="home",
        feed=news_db.get_dashboard_feed(filter=filter, source=source),
        top_news=news_db.get_top_news(),
        cve_watchlist=news_db.get_cve_watchlist(),
        sources=news_db.get_distinct_sources(),
        current_filter=filter,
        current_source=source or "",
    )

"""
sources page - GET lists sources, POST adds a new one (pending until
marked active in the database; ingestion-service polls active rows)
"""
source_db = SourceDB()
@routes.route("/sources", methods=["GET"])
def sources_route():
    return render_template("sources.html", sources=source_db.get_all_sources(), active_page="sources")
@routes.route("/sources", methods=["POST"])
def add_source_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "invalid request"}), 400
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    if not name or not url:
        return jsonify({"success": False, "message": "name and url are required"}), 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"success": False, "message": "please enter a valid url"}), 400
    result = source_db.create_source(name=name, url=url)
    if result is None:
        return jsonify({"success": False, "message": "something went wrong, please try again"}), 500
    if result is False:
        return jsonify({"success": False, "message": "that source already exists"}), 409
    return jsonify({"success": True, "message": "source added, pending activation"}), 200

"""
chat route - multi-turn dialogue via LangGraph agents
"""
@routes.route("/chat", methods=["POST"])
def chat_route():
    data = request.get_json()
    user_input = data.get("message", "")
    session_id = data.get("session_id", "default")
    article_id = data.get("article_id")

    if not user_input:
        return jsonify({"error": "message is required"}), 400

    history = _load_history(session_id)
    # grounding is single-turn: article_id is only present on the exact
    # request that came from clicking "Ask AI", nothing is persisted across
    # turns for it, follow-up messages behave like any other chat message
    active_article = news_db.get_article_by_id(article_id) if article_id else None
    force_grounded = active_article is not None
    from agents import agent_graph
    result = agent_graph.invoke({
        "user_input": user_input,
        "session_id": session_id,
        "chat_history": history,
        "notification_triggered": False,
        "active_article": active_article,
        "force_grounded": force_grounded,
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
