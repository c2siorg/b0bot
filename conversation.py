"""
Multi-turn conversation support for B0Bot.

Adds conversation memory so users can have back-and-forth
discussions about cybersecurity news instead of one-off queries.
"""

from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import uuid


class ConversationManager:
    """Handles multi-turn conversations with per-session memory."""

    def __init__(self, max_history=10):
        self.conversations = {}
        self.max_history = max_history

    def create_session(self):
        """Start a new chat session, returns its id."""
        sid = str(uuid.uuid4())
        self.conversations[sid] = ConversationBufferWindowMemory(
            k=self.max_history,
            return_messages=True,
            memory_key="chat_history",
        )
        return sid

    def get_or_create_session(self, session_id=None):
        """Return existing session or make a new one if missing."""
        if session_id and session_id in self.conversations:
            return session_id
        return self.create_session()

    def chat(self, session_id, llm, user_message, news_context=""):
        """Main method - send a message, get response with memory of past turns."""
        if session_id not in self.conversations:
            session_id = self.create_session()

        memory = self.conversations[session_id]

        # build system prompt - keeping it simple
        sys_prompt = (
            "You are B0Bot, a cybersecurity news assistant. "
            "Help users understand the latest threats, vulnerabilities, "
            "and security news. Keep answers concise and useful."
        )
        if news_context:
            sys_prompt += f"\n\nRecent news for context:\n{news_context}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        chain = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=prompt,
            input_key="input",
            verbose=False,
        )
        result = chain.invoke({"input": user_message})

        return {
            "session_id": session_id,
            "response": result.get("response", str(result)),
            "turn_count": len(memory.chat_memory.messages) // 2,
        }

    def get_history(self, session_id):
        """Get full chat history for a session."""
        if session_id not in self.conversations:
            return []

        msgs = self.conversations[session_id].chat_memory.messages
        return [
            {"role": "user" if m.type == "human" else "assistant",
             "content": m.content}
            for m in msgs
        ]

    def clear_session(self, session_id):
        """Wipe chat history but keep session alive."""
        if session_id in self.conversations:
            self.conversations[session_id].clear()
            return True
        return False

    def delete_session(self, session_id):
        """Remove a session entirely."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True
        return False


# single instance, imported by routes
conversation_manager = ConversationManager()
