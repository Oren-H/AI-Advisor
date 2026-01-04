# Load environment variables FIRST before any LangChain imports
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import uuid
import json
import asyncio
from langchain.messages import HumanMessage
from agent.graph.agent import get_course_advisor_agent
from agent.database_cache import db_cache

# Minimal message structure (frontend only needs role/content)
class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime

# Request/response models
class UserProfile(BaseModel):
    user_id: Optional[str] = Field(None, description="User ID")
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - runs on startup and shutdown
    """
    # STARTUP
    print("Starting up: Loading vector databases...")
    try:
        db_cache.load_course_df()
        db_cache.load_course_db()
        db_cache.load_bulletin_documents()
        db_cache.load_bulletin_db()
        print("All databases loaded successfully")
    except Exception as e:
        print(f"Error loading databases: {e}")
        # Continue with degraded functionality if bulletin DB fails
        # Course DB is critical, so it will raise if it fails

    yield  # App runs here

    # SHUTDOWN
    print("Shutting down: Cleaning up resources...")
    db_cache.close()
    print("Cleanup complete")

# FastAPI app
app = FastAPI(
    title="AI Advisor API",
    description="Minimal API with continuous conversation and SSE streaming",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for local dev and preview; tighten in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store
conversations: Dict[str, Dict[str, Any]] = {}
course_agent = get_course_advisor_agent()

@app.get("/", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        graph_ready=True, 
    )

def _create_default_user_profile() -> Dict[str, Any]:
    """Create a default user profile with empty/null values."""
    return {
        "user_id": None,
        "department_of_major": None,
        "major": None,
        "completed_courses": [],
        "semester": None,
        "career_goals": [],
        "preferences": []
    }

def _get_or_create_conversation(conversation_id: Optional[str], user_profile: Dict[str, Any]) -> str:
    conv_id = conversation_id or str(uuid.uuid4())
    if conv_id not in conversations:
        # Merge provided profile with defaults
        default_profile = _create_default_user_profile()
        merged_profile = user_profile if user_profile else default_profile

        conversations[conv_id] = {
            "history": [],  # List[Message]
            "user_profile": merged_profile,
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
        }
    return conv_id

def _append_message(conv_id: str, role: str, content: str) -> None:
    conversations[conv_id]["history"].append(
        Message(role=role, content=content, timestamp=datetime.now())
    )
    conversations[conv_id]["last_updated"] = datetime.now()

def _invoke_agent(conv_id: str, prompt: str, user_profile: Dict[str, Any]) -> str:
    """Invoke the course advisor agent from agent/graph/agent.py with thread-based memory."""
    # Map incoming user_profile to agent state fields if provided
    state_payload: Dict[str, Any] = {}
    allowed_keys = {"user_id", "department_of_major", "major", "completed_courses", "career_goals", "semester", "preferences"}
    for k, v in (user_profile or {}).items():
        if k in allowed_keys:
            state_payload[k] = v

    state_payload["user_id"] = "nl2951@columbia.edu"

    full_state = {
        "messages": [HumanMessage(content=prompt)],
        **state_payload,
    }

    result = course_agent.invoke(
        full_state,
        {"configurable": {"thread_id": conv_id}},
    )
    # Extract final assistant content
    messages = result.get("messages", [])
    if not messages:
        return ""
    last_msg = messages[-1]
    content = getattr(last_msg, "content", "")
    # Fallback if structure differs
    if isinstance(content, list):
        try:
            # Join parts if returned as content blocks
            content = "".join(getattr(part, "content", str(part)) for part in content)
        except Exception:
            content = str(content)
    return content

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        conv_id = _get_or_create_conversation(request.conversation_id, request.user_profile or {})
        _append_message(conv_id, "user", request.message)

        reply = _invoke_agent(conv_id, request.message, conversations[conv_id]["user_profile"])
        _append_message(conv_id, "assistant", reply)

        return ChatResponse(
            response=reply,
            conversation_id=conv_id,
            error=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            conv_id = _get_or_create_conversation(request.conversation_id, request.user_profile or {})
            _append_message(conv_id, "user", request.message)

            # Send initial metadata with conversation_id
            yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conv_id})}\n\n"

            # Invoke agent and get full response
            full_reply = _invoke_agent(conv_id, request.message, conversations[conv_id]['user_profile'])

            # Simulate streaming by splitting response into chunks
            for token in full_reply.split(" "):
                yield f"data: {json.dumps({'type': 'token', 'content': token + ' '})}\n\n"
                await asyncio.sleep(0.01)  # Small delay for UX

            _append_message(conv_id, "assistant", full_reply)

            # Final metadata payload (fields expected by frontend)
            final_meta = {
                "type": "metadata_final",
                "intent": "",
                "filters": {},
                "course_results": [],
                "error": "",
            }
            yield f"data: {json.dumps(final_meta)}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        },
    )

@app.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations():
    items: List[ConversationInfo] = []
    for cid, data in conversations.items():
        items.append(
            ConversationInfo(
                conversation_id=cid,
                created_at=data["created_at"],
                message_count=len(data["history"]),
                last_updated=data["last_updated"],
            )
        )
    items.sort(key=lambda x: x.last_updated, reverse=True)
    return items

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    data = conversations[conversation_id]
    return {
        "conversation_id": conversation_id,
        "created_at": data["created_at"],
        "last_updated": data["last_updated"],
        "message_count": len(data["history"]),
        "user_profile": data.get("user_profile", {}),
        "history": [m.dict() for m in data["history"]],
    }

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del conversations[conversation_id]
    return {"message": "Conversation deleted successfully"}

@app.delete("/conversations")
async def clear_all_conversations():
    conversations.clear()
    return {"message": "All conversations cleared successfully"}

@app.get("/conversations/{conversation_id}/profile")
async def get_user_profile(conversation_id: str):
    """Get the user profile for a conversation."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "conversation_id": conversation_id,
        "user_profile": conversations[conversation_id]["user_profile"]
    }

@app.put("/conversations/{conversation_id}/profile")
async def update_user_profile(conversation_id: str, profile: UserProfile):
    """Update the user profile for a conversation."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Update only the fields that are provided (non-None)
    current_profile = conversations[conversation_id]["user_profile"]
    updated_profile = profile.model_dump(exclude_unset=True)

    # Merge the updates into the current profile
    conversations[conversation_id]["user_profile"] = {**current_profile, **updated_profile}
    conversations[conversation_id]["last_updated"] = datetime.now()

    return {
        "message": "User profile updated successfully",
        "conversation_id": conversation_id,
        "user_profile": conversations[conversation_id]["user_profile"]
    }

@app.post("/profile/initialize")
async def initialize_user_profile(profile: UserProfile):
    """Initialize a new conversation with a user profile."""
    conv_id = str(uuid.uuid4())

    # Create conversation with the provided profile
    default_profile = _create_default_user_profile()
    merged_profile = {**default_profile, **profile.model_dump(exclude_none=True)}

    conversations[conv_id] = {
        "history": [],
        "user_profile": merged_profile,
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
    }

    return {
        "conversation_id": conv_id,
        "user_profile": merged_profile
    }


