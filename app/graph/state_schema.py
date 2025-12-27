from typing import Dict, List, Any, TypedDict, Annotated
from langchain.schema import BaseMessage
from operator import add

class UserProfile(TypedDict, total=False):
    """User profile with all optional fields."""
    department_of_major: str
    major: str
    completed_courses: List[str]
    career_goals: List[str]
    years_left: int
    preferences: Dict[str, Any]

# Define the state schema
class CourseAdvisorState(TypedDict):
    """State schema for the course advisor agent."""
    # Input/Output
    user_query: str
    response: str

    # Intent & Routing
    intent: str  # "specific", "advisory", "mixed", or "major"

    # Course Search - includes all fields used in nodes
    filters: Dict[str, Any]
    text_query: str  # Text query extracted from user input (used in generate_filters_node)
    course_results: List[Dict[str, Any]]
    course_info_json: str

    # Major Planning
    major_context: Dict[str, Any]  # Major requirements context (used in major_context_node)
    course_plan: str  # Generated course plan (used in plan_major_node)

    # Memory & Profile - using Annotated with add operator for automatic message appending
    conversation_history: Annotated[List[BaseMessage], add]  # Conversation context
    user_profile: UserProfile  # User preferences and context

    # Error handling
    error: str
    