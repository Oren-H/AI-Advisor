from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agent.database_cache import db_cache
from backend.agent.graph.agent import get_course_advisor_agent
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.messages import HumanMessage

from .schemas import (
    ChatRequest,
    ChatResponse,
    ConversationInfo,
    HealthResponse,
    Message,
    UserProfile,
    UserProfileUpdateRequest,
)

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "agent" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# API logger - for HTTP requests and database operations
API_LOG_FILE = LOG_DIR / "api.log"
api_logger = logging.getLogger("api")
api_logger.setLevel(logging.INFO)
api_handler = logging.FileHandler(API_LOG_FILE)
api_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
api_logger.addHandler(api_handler)
api_logger.addHandler(logging.StreamHandler())

# Agent logger - for AI tools and streaming operations
AGENT_LOG_FILE = LOG_DIR / "agent.log"
agent_logger = logging.getLogger("agent")
agent_logger.setLevel(logging.INFO)
agent_handler = logging.FileHandler(AGENT_LOG_FILE)
agent_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
agent_logger.addHandler(agent_handler)
agent_logger.addHandler(logging.StreamHandler())

# Tools logger - for tool execution and debugging
TOOLS_LOG_FILE = LOG_DIR / "tools.log"
tools_logger = logging.getLogger("tools")
tools_logger.setLevel(logging.INFO)
tools_handler = logging.FileHandler(TOOLS_LOG_FILE)
tools_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
tools_logger.addHandler(tools_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - runs on startup and shutdown
    """
    # STARTUP
    api_logger.info("Starting up: Loading vector databases...")
    try:
        db_cache.load_course_df()
        db_cache.load_course_db()
        db_cache.load_bulletin_documents()
        db_cache.load_bulletin_db()
        api_logger.info("All databases loaded successfully")
    except Exception as e:
        api_logger.error(f"Error loading databases: {e}")
        # Continue with degraded functionality if bulletin DB fails
        # Course DB is critical, so it will raise if it fails

    yield  # App runs here

    # SHUTDOWN
    api_logger.info("Shutting down: Cleaning up resources...")
    db_cache.close()
    api_logger.info("Cleanup complete")


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
        "name": None,
        "school": None,
        "department_of_major": None,
        "major": None,
        "completed_courses": [],
        "semester": None,
        "career_goals": [],
        "preferences": [],
    }


def _get_or_create_conversation(conversation_id: Optional[str], user_profile: Dict[str, Any]) -> str:
    conv_id = conversation_id or str(uuid.uuid4())
    if conv_id not in conversations:
        # Merge provided profile with defaults
        profile = user_profile if user_profile else _create_default_user_profile()

        conversations[conv_id] = {
            "history": [],  # List[Message]
            "user_profile": profile,
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
    allowed_keys = {"user_id", "name", "school", "department_of_major", "major", "completed_courses", "career_goals", "semester", "preferences"}
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
        {
            "configurable": {"thread_id": conv_id},
            "recursion_limit": 50,  # guardrail to avoid runaway loops
        },
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
        api_logger.info(f"Chat request received for conversation {conv_id}")
        _append_message(conv_id, "user", request.message)

        reply = _invoke_agent(conv_id, request.message, conversations[conv_id]["user_profile"])

        _append_message(conv_id, "assistant", reply)
        api_logger.info(f"Chat response sent for conversation {conv_id}")

        return ChatResponse(
            response=reply,
            conversation_id=conv_id,
            error=None,
        )
    except Exception as e:
        api_logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            conv_id = _get_or_create_conversation(request.conversation_id, request.user_profile or {})
            api_logger.info(f"Stream chat request received for conversation {conv_id}")
            _append_message(conv_id, "user", request.message)

            # Send initial metadata with conversation_id
            yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conv_id})}\n\n"

            # Prepare state
            state_payload: Dict[str, Any] = {}
            allowed_keys = {"user_id", "name", "school", "department_of_major", "major",
                            "completed_courses", "career_goals", "semester", "preferences"}
            for k, v in (conversations[conv_id]["user_profile"] or {}).items():
                if k in allowed_keys:
                    state_payload[k] = v
            state_payload["user_id"] = "nl2951@columbia.edu"

            full_state = {
                "messages": [HumanMessage(content=request.message)],
                **state_payload,
            }

            full_reply = ""
            agent_logger.info(f"Starting agent stream for conversation {conv_id}, Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Use astream for async streaming with messages and custom modes
            async for event in course_agent.astream_events(
                    full_state,
                    {
                        "configurable": {"thread_id": conv_id},
                        "recursion_limit": 50,  # guardrail to avoid runaway loops
                    },
                    version="v2",  # Use v2 for consistent events
                ):
                    # Filter for LLM token events
                    agent_logger.info(event)

                    if event["event"] == "on_chat_model_stream":
                        # Skip streaming LLM calls from within tools (e.g., filter generation)
                        # Only stream the main agent's response
                        metadata = event.get("metadata", {})
                        if metadata.get("langgraph_node") == "tools":
                            continue

                        chunk = event["data"]["chunk"]

                        # Only stream text if this message doesn't contain tool calls
                        # This ensures we only stream the final response, not intermediate text
                        has_tool_calls = False
                        if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                            has_tool_calls = True
                        elif isinstance(chunk.content, list):
                            # Check if any content blocks are tool_use
                            has_tool_calls = any(
                                isinstance(part, dict) and part.get("type") in ("tool_use", "tool_result")
                                for part in chunk.content
                            )

                        # TEXT TOKENS - only stream and save if no tool calls in this message
                        # This ensures intermediate text during tool calls is ignored
                        if chunk.content and not has_tool_calls:
                            # Handle string content
                            if isinstance(chunk.content, str):
                                full_reply += chunk.content
                                yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                            # Handle list of content blocks
                            elif isinstance(chunk.content, list):
                                for part in chunk.content:
                                    # Only process text blocks
                                    if isinstance(part, dict):
                                        if part.get("type") == "text" and "text" in part:
                                            text = part["text"]
                                            full_reply += text
                                            yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"
                                    # If part is a string (shouldn't happen but be defensive)
                                    elif isinstance(part, str):
                                        full_reply += part
                                        yield f"data: {json.dumps({'type': 'token', 'content': part})}\n\n"

                    # TOOL START
                    elif event["event"] == "on_tool_start":
                        try:
                            tool_name = event.get("name")
                            tool_input = event.get("data", {}).get("input")
                            payload: Dict[str, Any] = {"type": "tool", "tool": tool_name}
                            if tool_input is not None:
                                payload["input"] = tool_input
                            yield f"data: {json.dumps(payload)}\n\n"
                        except Exception:
                            pass
                    # TOOL END 
                    elif event["event"] == "on_tool_end":
                        try:
                            tool_name = event.get("name")
                            output_obj = event.get("data", {}).get("output")
                            # Extract content safely
                            if hasattr(output_obj, "content"):
                                content = getattr(output_obj, "content")
                            else:
                                content = output_obj
                            if content is None:
                                continue
                            if not isinstance(content, str):
                                try:
                                    content = json.dumps(content)
                                except Exception:
                                    content = str(content)
                            max_len = 2000
                            output = content if len(content) <= max_len else (content[:max_len] + "...(truncated)")
                            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'output': output})}\n\n"
                        except Exception:
                            pass

            _append_message(conv_id, "assistant", full_reply)
            api_logger.info(f"Stream chat response completed for conversation {conv_id}")

            # Just signal we're done
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

        except Exception as e:
            api_logger.error(f"Error in stream chat endpoint: {str(e)}", exc_info=True)
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
    profile_dict = profile.model_dump() if profile else _create_default_user_profile()

    conversations[conv_id] = {
        "history": [],
        "user_profile": profile_dict,
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
    }

    return {
        "conversation_id": conv_id,
        "user_profile": profile_dict
    }


