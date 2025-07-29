from typing import List
from langchain.schema import HumanMessage, AIMessage

def generate_conversation_context(history: List, max_messages: int = 8) -> str:
    """
    Generate conversation context from message history.
    
    Args:
        history: List of conversation messages
        max_messages: Maximum number of recent messages to include (default: 8)
    
    Returns:
        Formatted conversation context string
    """
    if not history:
        return ""
    
    # Get recent messages (last max_messages * 2 to account for user/ai pairs)
    recent_history = history[-(max_messages * 2):] if len(history) > (max_messages * 2) else history
    
    # Format messages as conversation
    conversation_context = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" 
        for msg in recent_history
    ])
    
    return conversation_context 