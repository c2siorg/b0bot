"""
Flask routes for the multi-turn chat feature.
Register this blueprint in app.py to enable /chat endpoints.
"""

from flask import Blueprint, request, jsonify
from conversation import conversation_manager

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/<llm_name>/chat", methods=["POST"])
def chat(llm_name):
    """
    POST JSON with {"message": "your question", "session_id": "optional"}
    Returns {"session_id": "...", "response": "...", "turn_count": N}

    First call: don't pass session_id, you'll get one back.
    Follow-up calls: pass the session_id to continue the conversation.
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Need a 'message' field in JSON body"}), 400

    user_msg = data["message"]
    sid = data.get("session_id")

    sid = conversation_manager.get_or_create_session(sid)

    # load the right LLM - reusing whatever b0bot already has
    try:
        from controllers.llm_controller import load_llm
        llm = load_llm(llm_name)
    except (ImportError, Exception) as e:
        return jsonify({
            "error": f"Couldn't load LLM '{llm_name}': {str(e)}. "
                     f"Try: llama, gemma, or mistralai"
        }), 400

    # try to pull relevant news as context
    news_ctx = ""
    try:
        from services.news_service import get_recent_news
        news_ctx = get_recent_news(keywords=user_msg)
    except Exception:
        pass  # no news context is fine, chat still works

    result = conversation_manager.chat(sid, llm, user_msg, news_ctx)
    return jsonify(result)


@chat_bp.route("/chat/history/<session_id>", methods=["GET"])
def get_history(session_id):
    """Get the conversation history for a session."""
    history = conversation_manager.get_history(session_id)
    return jsonify({"session_id": session_id, "history": history})


@chat_bp.route("/chat/clear/<session_id>", methods=["POST"])
def clear_history(session_id):
    """Clear chat history for a session (keeps session alive)."""
    ok = conversation_manager.clear_session(session_id)
    return jsonify({"session_id": session_id, "cleared": ok})
