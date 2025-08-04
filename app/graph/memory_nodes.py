import os
import json
from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage
from app.graph.state_schema import CourseAdvisorState
from app.prompt_manager import prompt_manager
from app.llm_manager import llm_manager
from app.graph.conversation_utils import generate_conversation_context

def update_memory_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Update conversation memory and extract user profile information."""
    try:
        print(f"🧠 Updating memory for query: {state['user_query']}")
        
        # Get current conversation history
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Add the current user query to history
        history.append(HumanMessage(content=state["user_query"]))
        
        # Create prompt template from the profile extraction prompt
        profile_prompt = ChatPromptTemplate.from_template(prompt_manager.get_prompt("profile_extraction"))
        
        # Get shared LLM instance for profile extraction
        llm = llm_manager.get_llm(model_provider="openai", temperature=0)
        
        # Create a chain using the pipe operator
        profile_chain = profile_prompt | llm
        
        # Prepare conversation context (last 3 exchanges for context)
        conversation_context = generate_conversation_context(history, max_messages=3)
        
        # Run the chain with the input variables
        profile_response = profile_chain.invoke({
            "conversation_context": conversation_context,
            "user_query": state["user_query"]
        })
        
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