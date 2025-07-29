import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage
from app.graph.state_schema import CourseAdvisorState
from app.prompt_manager import prompt_manager

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def update_memory_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Update conversation memory and extract user profile information."""
    try:
        print(f"🧠 Updating memory for query: {state['user_query']}")
        
        # Get current conversation history
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Add the current user query to history
        history.append(HumanMessage(content=state["user_query"]))
        
        # Extract user profile information from the query
        profile_prompt = ChatPromptTemplate.from_template(prompt_manager.get_prompt("profile_extraction"))
        
        # Initialize the LLM for profile extraction
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.1
        )
        
        # Prepare conversation context (last 3 exchanges for context)
        recent_history = history[-6:] if len(history) > 6 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Format the prompt with variables
        formatted_prompt = profile_prompt.format_prompt(
            conversation_context=conversation_context,
            user_query=state["user_query"]
        )
        
        # Extract profile information
        profile_response = llm.invoke(formatted_prompt)
        
        try:
            new_profile_info = json.loads(profile_response.content)
            # Merge with existing profile
            user_profile.update(new_profile_info)
        except json.JSONDecodeError:
            print("⚠️ Could not parse profile information")
        
        print(f"✅ Updated memory with {len(history)} messages, profile: {user_profile}")
        return {**state, "conversation_history": history, "user_profile": user_profile, "error": ""}
        
    except Exception as e:
        print(f"❌ Error updating memory: {e}")
        return {**state, "error": f"Failed to update memory: {str(e)}"}

def finalize_memory_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Add the AI response to conversation history and finalize the memory."""
    try:
        print(f"💾 Finalizing memory with AI response")
        
        # Get current conversation history
        history = state.get("conversation_history", [])
        
        # Add the AI response to history
        history.append(AIMessage(content=state["response"]))
        
        # Keep only the last 20 messages to prevent memory from growing too large
        if len(history) > 20:
            history = history[-20:]
        
        print(f"✅ Finalized memory with {len(history)} total messages")
        return {**state, "conversation_history": history, "error": ""}
        
    except Exception as e:
        print(f"❌ Error finalizing memory: {e}")
        return {**state, "error": f"Failed to finalize memory: {str(e)}"} 