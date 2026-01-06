from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime


class UserProfile(BaseModel):
    user_id: Optional[str] = Field(None, description="User ID")
    name: Optional[str] = Field(None, description="User's name")
    school: Optional[str] = Field(None, description="School (e.g., 'SEAS', 'GS', 'CC')")
    department_of_major: Optional[str] = Field(None, description="Department of major (e.g., 'COMS', 'MATH')")
    major: Optional[str] = Field(None, description="Major name (e.g., 'Computer Science', 'Applied Mathematics')")
    completed_courses: List[str] = Field(default_factory=list, description="List of completed course codes")
    semester: Optional[int] = Field(None, description="Current semester (1-8)")
    career_goals: List[str] = Field(default_factory=list, description="Career goals (e.g., ['Software Engineering', 'Quantitative Finance'])")
    preferences: List[str] = Field(default_factory=list, description="User preferences (e.g., ['classes after 10am', 'small class sizes'])")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message/query")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID for continuity")
    user_profile: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User profile information")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID for future interactions")
    error: Optional[str] = Field(None, description="Error message if any")


class UserProfileUpdateRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID to update profile for")
    user_profile: UserProfile = Field(..., description="Updated user profile")


class ConversationInfo(BaseModel):
    conversation_id: str
    created_at: datetime
    message_count: int
    last_updated: datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    graph_ready: bool


