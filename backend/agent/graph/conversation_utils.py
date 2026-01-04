from typing import List
from langchain.messages import SystemMessage
from langchain.messages import HumanMessage

def generate_conversation_context(history: List, max_messages: int = 8) -> str:
    """
    Generate conversation context from message history.

    Args:
        history: List of conversation messages (can be strings or Message objects)
        max_messages: Maximum number of recent messages to include (default: 8)

    Returns:
        Formatted conversation context string
    """
    if not history:
        return ""

    # Get recent messages (last max_messages * 2 to account for user/ai pairs)
    recent_history = history[-(max_messages * 2):] if len(history) > (max_messages * 2) else history

    # Format messages as conversation
    formatted_messages = []
    for msg in recent_history:
        # Handle both string and Message object types
        if isinstance(msg, str):
            formatted_messages.append(f"User: {msg}")
        elif hasattr(msg, 'content'):
            # Message object with content attribute
            role = 'User' if isinstance(msg, HumanMessage) else 'AI'
            formatted_messages.append(f"{role}: {msg.content}")
        else:
            # Fallback for unknown types
            formatted_messages.append(f"Message: {str(msg)}")

    conversation_context = "\n".join(formatted_messages)

    return conversation_context 

def dump_messages_pretty(messages):
    """
    Dump messages to the console in a pretty format.
    """
    for i, m in enumerate(messages, 1):
        print("\n" + "="*80)
        print(f"[{i}] {m.__class__.__name__}")
        try:
            m.pretty_print()
        except Exception:
            # fallback
            print(getattr(m, "content", m))