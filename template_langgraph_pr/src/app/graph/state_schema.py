from typing import Dict, List, Any, TypedDict, Annotated
from langchain.schema import BaseMessage
from operator import add

class IntentRoute(TypedDict, total=False):
    """Intent route"""
    intent: Literal["major_search", "course_search", "general"] = Field(None, 
        description="Figuring out the intent of the user query") 
    reasoning: str = Field(None, description="Brief explanation of why this intent was chosen") 

# Define the state schema
class CourseAdvisorState(TypedDict, total=False):
    """State schema for the course advisor agent."""
    # Input/OutpuT
    user_query: str # user gives 
    agent_response: str # agent response 
    
    # Memory
    messages: Annotated[List[BaseMessage], add]

    # LLM Calls
    llm_calls: int
    llm_optimized_query: str

    # Course Search
    course_results: List[Dict[str, Any]]

    # Major Search
    major_requirements: MajorRequirements
    
    
class UserProfile(TypedDict, total=False):
    """User profile"""

    department_of_major: str
    major: str
    completed_courses: List[str]
    career_goals: List[str]
    semester: str
    preferences: Dict[str, Any]

class MajorRequirements(TypedDict, total=False):
    """Major requirements"""
    major: UserProfile["major"]
    major_requirements: str
    schedule: Dict[str, Any]