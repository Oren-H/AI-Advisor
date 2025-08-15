from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

from app.graph.graph_builder import create_course_advisor_graph
from app.graph.simpler_graph_builder import create_simplified_course_advisor_graph
from app.graph.state_schema import CourseAdvisorState
from langchain.schema import HumanMessage, AIMessage

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
            "course_results": [],
            "course_info_json": "",
            "response": "",
            "error": "",
            "conversation_history": conversation_history,
            "user_profile": user_profile
        }
        
        # Run the graph
        print(f"🚀 Processing query: {request.message}")
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
        
        print(f"✅ Response generated for conversation {conversation_id}")
        return response
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint for real-time response generation"""
    async def generate_stream():
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
                "course_results": [],
                "course_info_json": "",
                "response": "",
                "error": "",
                "conversation_history": conversation_history,
                "user_profile": user_profile
            }
            
            # Run the graph
            print(f"🚀 Processing streaming query: {request.message}")
            final_state = await course_advisor_graph.ainvoke(initial_state)
            
            # Update conversation storage
            conversations[conversation_id]["history"] = final_state["conversation_history"]
            conversations[conversation_id]["user_profile"] = final_state["user_profile"]
            conversations[conversation_id]["last_updated"] = datetime.now()
            
            # Stream the response character by character
            response_text = final_state["response"]
            
            # Send metadata first
            metadata = {
                "type": "metadata",
                "conversation_id": conversation_id,
                "intent": final_state["intent"],
                "course_results": final_state.get("course_results"),
                "filters": final_state.get("filters"),
                "error": final_state.get("error")
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream the response text
            for char in response_text:
                yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                # Small delay to simulate real streaming
                import asyncio
                await asyncio.sleep(0.02)  # 20ms delay
            
            # Send end marker
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
        except Exception as e:
            print(f"❌ Error in streaming chat endpoint: {e}")
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 