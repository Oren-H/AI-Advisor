from typing import Dict, List, Any, TypedDict
from langchain.schema import BaseMessage

# Define the state schema
class CourseAdvisorState(TypedDict):
    user_query: str
    intent: str  # "specific", "advisory", or "mixed"
    filters: Dict[str, Any]
    course_results: List[Dict[str, Any]]
    course_info_json: str
    response: str
    error: str
    conversation_history: List[BaseMessage]  # Memory for conversation context
    user_profile: Dict[str, Any]  # Store user preferences and context 