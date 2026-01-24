import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.graph.graph_builder import create_course_advisor_graph
from agent.graph.state_schema import CourseAdvisorState
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.schema import HumanMessage
from pydantic import BaseModel, Field

# Initialize FastAPI app
app = FastAPI(
    title="Course Advisor API",
    description="AI-powered course recommendation and advisory system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the graph
course_advisor_graph = create_course_advisor_graph()

# In-memory storage for conversations (use a proper database in production)
conversations: Dict[str, Dict[str, Any]] = {}

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message/query")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID for continuity")
    user_profile: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User profile information")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID for future interactions")
    intent: str = Field(..., description="Classified intent of the user query")
    course_results: Optional[List[Dict[str, Any]]] = Field(None, description="Course search results if applicable")
    filters: Optional[Dict[str, Any]] = Field(None, description="Generated filters if applicable")
    error: Optional[str] = Field(None, description="Error message if any")

class ConversationInfo(BaseModel):
    conversation_id: str
    created_at: datetime
    message_count: int
    last_updated: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    graph_ready: bool

class UserProfileRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID to associate profile with")
    department_of_major: str = Field(..., description="Department code (e.g., 'MATH', 'COMS')")
    major: str = Field(..., description="Full major name (e.g., 'Major in Applied Mathematics')")
    completed_courses: List[str] = Field(default_factory=list, description="List of completed course codes")
    years_left: int = Field(default=4, description="Years left until graduation")
    career_goals: List[str] = Field(default_factory=list, description="Career interests/goals")

class UserProfileResponse(BaseModel):
    conversation_id: str
    profile: Dict[str, Any]
    message: str

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        graph_ready=course_advisor_graph is not None
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for course advisor interactions"""
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get or create conversation history
        if conversation_id in conversations:
            conversation_history = conversations[conversation_id]["history"]
            user_profile = conversations[conversation_id].get("user_profile", {})
        else:
            conversation_history = []
            user_profile = request.user_profile or {}
            conversations[conversation_id] = {
                "history": conversation_history,
                "user_profile": user_profile,
                "created_at": datetime.now(),
                "last_updated": datetime.now()
            }
        
        # Prepare initial state
        initial_state: CourseAdvisorState = {
            "user_query": request.message,
            "intent": "",
            "filters": {},
            "text_query": "",  # Added missing field
            "course_results": [],
            "course_info_json": "",
            "response": "",
            "error": "",
            "conversation_history": conversation_history,
            "user_profile": user_profile,
            "major_context": {},  # Added missing field
            "course_plan": "",  # Added missing field
        }
        
        # Run the graph
        print(f"Processing query: {request.message}")
        final_state = await course_advisor_graph.ainvoke(initial_state)
        
        # Update conversation storage
        conversations[conversation_id]["history"] = final_state["conversation_history"]
        conversations[conversation_id]["user_profile"] = final_state["user_profile"]
        conversations[conversation_id]["last_updated"] = datetime.now()
        
        # Prepare response
        response = ChatResponse(
            response=final_state["response"],
            conversation_id=conversation_id,
            intent=final_state["intent"],
            course_results=final_state.get("course_results"),
            filters=final_state.get("filters"),
            error=final_state.get("error")
        )
        
        print(f"Response generated for conversation {conversation_id}")
        return response
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint with REAL LLM token streaming using astream_events"""
    async def generate_stream():
        conversation_id = None
        final_state = None

        try:
            # ------------------------------------------------------------------
            # 1. Conversation setup
            # ------------------------------------------------------------------
            conversation_id = request.conversation_id or str(uuid.uuid4())

            # Get or create conversation history
            if conversation_id in conversations:
                conversation_history = conversations[conversation_id]["history"]
                user_profile = conversations[conversation_id].get("user_profile", {})
            else:
                conversation_history = []
                user_profile = request.user_profile or {}
                conversations[conversation_id] = {
                    "history": conversation_history,
                    "user_profile": user_profile,
                    "created_at": datetime.now(),
                    "last_updated": datetime.now(),
                }

            # Prepare initial state
            initial_state: CourseAdvisorState = {
                "user_query": request.message,
                "intent": "",  # intent not used in simplified graph
                "filters": {},
                "text_query": "",
                "course_results": [],
                "course_info_json": "",
                "response": "",
                "error": "",
                "conversation_history": conversation_history,
                "user_profile": user_profile,
                "major_context": {},
                "course_plan": "",
            }

            print(f"Processing streaming query: {request.message}")

            # Send initial metadata with conversation_id
            metadata = {
                "type": "metadata",
                "conversation_id": conversation_id,
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # Use astream_events for REAL streaming of LLM tokens
            async for event in course_advisor_graph.astream_events(
                initial_state,
                version="v2"
            ):
                kind = event["event"]

                # Stream LLM tokens as they're generated (REAL streaming!)
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, 'content') and chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

                # Send node execution updates for progress tracking
                elif kind == "on_chain_start":
                    node_name = event.get("name", "")
                    if node_name:
                        print(f"  Node started: {node_name}")
                        yield f"data: {json.dumps({'type': 'node_start', 'node': node_name})}\n\n"

                elif kind == "on_chain_end":
                    node_name = event.get("name", "")

                    # Capture final state from the last node
                    if node_name == "finalize_memory":
                        final_state = event["data"].get("output")
                        if final_state:
                            print("  Graph execution complete")
                            # Update conversation storage
                            conversations[conversation_id]["history"] = final_state.get("conversation_history", conversation_history)
                            conversations[conversation_id]["user_profile"] = final_state.get("user_profile", user_profile)
                            conversations[conversation_id]["last_updated"] = datetime.now()

                            # Send final metadata with intent, filters, and results
                            final_metadata = {
                                "type": "metadata_final",
                                "intent": final_state.get("intent", ""),
                                "filters": final_state.get("filters", {}),
                                "course_results": final_state.get("course_results", []),
                                "error": final_state.get("error", "")
                            }
                            yield f"data: {json.dumps(final_metadata)}\n\n"

                    if node_name:
                        print(f"  Node completed: {node_name}")

            # Send end marker
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            print(f"Streaming complete for conversation {conversation_id}")

        except Exception as e:
            print(f"Error in streaming chat endpoint: {e}")
            import traceback
            traceback.print_exc()
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )

@app.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations():
    """List all active conversations"""
    conversation_list = []
    for conv_id, conv_data in conversations.items():
        conversation_list.append(ConversationInfo(
            conversation_id=conv_id,
            created_at=conv_data["created_at"],
            message_count=len(conv_data["history"]),
            last_updated=conv_data["last_updated"]
        ))
    
    # Sort by last updated (most recent first)
    conversation_list.sort(key=lambda x: x.last_updated, reverse=True)
    return conversation_list

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get details of a specific conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv_data = conversations[conversation_id]
    return {
        "conversation_id": conversation_id,
        "created_at": conv_data["created_at"],
        "last_updated": conv_data["last_updated"],
        "message_count": len(conv_data["history"]),
        "user_profile": conv_data.get("user_profile", {}),
        "history": [
            {
                "type": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
                "timestamp": conv_data["created_at"]  # You might want to add actual timestamps
            }
            for msg in conv_data["history"]
        ]
    }

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations[conversation_id]
    return {"message": "Conversation deleted successfully"}

@app.delete("/conversations")
async def clear_all_conversations():
    """Clear all conversations (use with caution)"""
    conversations.clear()
    return {"message": "All conversations cleared successfully"}

@app.get("/conversations/{conversation_id}/profile")
async def get_user_profile(conversation_id: str):
    """Get the user profile for a specific conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "user_profile": conversations[conversation_id].get("user_profile", {})
    }

@app.put("/conversations/{conversation_id}/profile")
async def update_user_profile(conversation_id: str, profile: Dict[str, Any]):
    """Update the user profile for a specific conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversations[conversation_id]["user_profile"] = profile
    conversations[conversation_id]["last_updated"] = datetime.now()
    
    return {
        "conversation_id": conversation_id,
        "user_profile": profile,
        "message": "Profile updated successfully"
    }

@app.post("/profile", response_model=UserProfileResponse)
async def set_user_profile(request: UserProfileRequest):
    """Set structured user profile for a conversation"""
    conversation_id = request.conversation_id
    
    # Create conversation if it doesn't exist
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "history": [],
            "user_profile": {},
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
    
    # Structure the profile data
    profile_data = {
        "department_of_major": request.department_of_major,
        "major": request.major,
        "completed_courses": request.completed_courses,
        "years_left": request.years_left,
        "career_goals": request.career_goals
    }
    
    # Validate major exists (using our generate_major_context function)
    try:
        from major_scraping.generate_major_context import generate_major_context
        generate_major_context(request.department_of_major, request.major)
        validation_message = "Profile set successfully and major validated"
    except ValueError as e:
        validation_message = f"Profile set successfully but major validation failed: {str(e)}"
    
    # Update the conversation
    conversations[conversation_id]["user_profile"] = profile_data
    conversations[conversation_id]["last_updated"] = datetime.now()
    
    return UserProfileResponse(
        conversation_id=conversation_id,
        profile=profile_data,
        message=validation_message
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 