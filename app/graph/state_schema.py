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

    # New fields for major planning path
    dept_html: str  # Full department HTML (overview + requirements)
    course_plan: Dict[str, Any]  # Finalized YAML after lightweight validation
    quotes: List[str]  # Verbatim HTML quotes used to justify numbers/levels
    