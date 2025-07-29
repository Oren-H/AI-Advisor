import os
import json
from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage

# Import our existing modules using absolute imports
from app.db_querying.generate_filters import generate_filters_from_prompt
from app.db_querying.query_courses_from_filter import query_courses_with_filters
from app.graph.state_schema import CourseAdvisorState
from app.prompt_manager import prompt_manager
from app.llm_manager import llm_manager

def intent_classification_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Classify the user's intent based on their query and conversation history."""
    try:
        print(f"🧠 Classifying intent for query: {state['user_query']}")
        
        # Get conversation history for context
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 4 exchanges for context)
        recent_history = history[-8:] if len(history) > 8 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Create a prompt for intent classification with memory
        intent_prompt = ChatPromptTemplate.from_template(prompt_manager.get_prompt("intent_classification"))
        
        # Get shared LLM instance
        llm = llm_manager.get_intent_classification_llm()
        
        # Create the chain
        chain = intent_prompt | llm
        
        # Classify intent
        intent_response = chain.invoke({
            "user_query": state['user_query'],
            "conversation_context": conversation_context,
            "user_profile": json.dumps(user_profile, indent=2)
        })
        intent = intent_response.content.strip().upper()
        
        # Validate the response
        if intent not in ["SPECIFIC", "ADVISORY", "MIXED"]:
            # Default to mixed if classification is unclear
            intent = "MIXED"
        
        print(f"✅ Classified intent as: {intent}")
        return {**state, "intent": intent.lower(), "error": ""}
        
    except Exception as e:
        print(f"❌ Error classifying intent: {e}")
        return {**state, "intent": "mixed", "error": f"Failed to classify intent: {str(e)}"}

def generate_filters_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate metadata filters from user query using the existing generate_filters module."""
    try:
        print(f"🔍 Generating filters for query: {state['user_query']}")
        
        # Get conversation history for context
        history = state.get("conversation_history", [])
        
        # Prepare conversation context (last 6 exchanges for context)
        recent_history = history[-12:] if len(history) > 12 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Add conversation context to help with follow-up questions
        if conversation_context:
            conversation_context = f"Conversation Context:\n{conversation_context}\n"
        
        filters = generate_filters_from_prompt(state['user_query'], conversation_context)
        print(f"✅ Generated filters: {filters}")
        return {**state, "filters": filters, "error": ""}
    except Exception as e:
        print(f"❌ Error generating filters: {e}")
        return {**state, "filters": {}, "error": f"Failed to generate filters: {str(e)}"}

def search_courses_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Search for courses using the generated filters and vector search."""
    try:
        print(f"🔎 Searching courses with filters: {state['filters']}")
        
        # Get conversation history for context
        history = state.get("conversation_history", [])
        
        # Prepare conversation context (last 6 exchanges for context)
        recent_history = history[-12:] if len(history) > 12 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Use the filters from the previous node
        course_results = query_courses_with_filters(
            state['user_query'], 
            filters=state['filters'], 
            k=5,
            conversation_context=conversation_context
        )
        
        # Convert to JSON string for the conversational agent
        course_info_json = json.dumps(course_results, indent=2)
        
        print(f"✅ Found {len(course_results)} courses")
        return {**state, "course_results": course_results, "course_info_json": course_info_json, "error": ""}
        
    except Exception as e:
        print(f"❌ Error searching courses: {e}")
        return {**state, "course_results": [], "course_info_json": "[]", "error": f"Failed to search courses: {str(e)}"}

def advisory_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate advisory response without course search, using conversation memory."""
    try:
        print(f"💡 Generating advisory response for intent: {state['intent']}")
        
        # Get conversation history and user profile
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 6 exchanges for context)
        recent_history = history[-12:] if len(history) > 12 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Create an advisory-focused prompt template with memory
        advisory_prompt = ChatPromptTemplate.from_template(prompt_manager.get_prompt("advisory_response"))
        
        # Get shared LLM instance
        llm = llm_manager.get_advisory_llm()
        
        # Create the chain
        chain = advisory_prompt | llm
        
        # Generate response
        response = chain.invoke({
            "user_query": state["user_query"],
            "conversation_context": conversation_context,
            "user_profile": json.dumps(user_profile, indent=2)
        })
        
        print(f"✅ Generated advisory response")
        return {**state, "response": response.content, "error": ""}
        
    except Exception as e:
        print(f"❌ Error generating advisory response: {e}")
        return {**state, "response": f"I encountered an error while generating advisory guidance: {str(e)}", "error": str(e)}

def generate_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate the final response using the conversational agent template with memory."""
    try:
        if state.get("error"):
            return {**state, "response": f"I encountered an error: {state['error']}. Please try rephrasing your query."}
        
        if not state.get("course_results"):
            return {**state, "response": "I couldn't find any courses matching your criteria. Please try broadening your search or rephrasing your query."}
        
        # Get conversation history and user profile
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 6 exchanges for context)
        recent_history = history[-12:] if len(history) > 12 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Choose prompt template based on intent
        if state.get("intent") == "mixed":
            # Mixed intent: combine advisory guidance with course recommendations
            prompt_template = ChatPromptTemplate.from_template(prompt_manager.get_prompt("mixed_response"))
        else:
            # Specific intent: focus on course recommendations
            prompt_template = ChatPromptTemplate.from_template(prompt_manager.get_prompt("specific_response"))
        
        # Get shared LLM instance
        llm = llm_manager.get_response_llm()
        
        # Create the chain
        chain = prompt_template | llm
        
        # Generate response
        response = chain.invoke({
            "course_info": state["course_info_json"],
            "user_query": state["user_query"],
            "conversation_context": conversation_context,
            "user_profile": json.dumps(user_profile, indent=2)
        })
        
        print(f"✅ Generated response for user query")
        return {**state, "response": response.content, "error": ""}
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return {**state, "response": f"I encountered an error while generating a response: {str(e)}", "error": str(e)}

def route_by_intent(state: CourseAdvisorState) -> str:
    """Route to different paths based on the user's intent."""
    intent = state.get("intent", "mixed")
    
    if intent == "advisory":
        return "advisory_response"
    elif intent == "specific":
        return "generate_filters"
    else:  # mixed
        return "generate_filters" 