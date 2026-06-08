from typing import TypedDict, Optional, List

class PlannerState(TypedDict):
    user_input: str
    intent: Optional[str]
    keywords: Optional[List[str]]
    retrieved_articles: Optional[List[dict]]
    llm_response: Optional[str]
    session_id: Optional[str]
    chat_history: Optional[List[dict]]
    notification_triggered: bool
