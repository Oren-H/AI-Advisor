import os
import json
from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
import logging

# Import our existing modules using absolute imports
from app.db_querying.generate_filters import generate_filters_from_prompt
from app.db_querying.query_courses_from_filter import query_courses_with_filters
from app.graph.state_schema import CourseAdvisorState
from app.graph.conversation_utils import generate_conversation_context
from app.prompt_manager import prompt_manager
from app.llm_manager import llm_manager
from app.utils.timed_step import timed_step

@timed_step("generate_filters")
def generate_filters_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate metadata filters from user query using the existing generate_filters module."""
    try:
        print(f"🔍 Generating filters for query: {state['user_query']}")
        
        # Get conversation history for context
        history = state.get("conversation_history", [])
        
        # Prepare conversation context (last 6 exchanges for context)
        conversation_context = generate_conversation_context(history, max_messages=6)
        
        # Add conversation context to help with follow-up questions
        if conversation_context:
            conversation_context = f"Conversation Context:\n{conversation_context}\n"
        
        filters, text_query = generate_filters_from_prompt(state['user_query'], conversation_context)
        print(f"✅ Generated filters: {filters}")
        print(f"✅ Generated text query: {text_query}")
        return {**state, "filters": filters, "text_query": text_query, "error": ""}
    except Exception as e:
        print(f"❌ Error generating filters: {e}")
        return {**state, "filters": {}, "error": f"Failed to generate filters: {str(e)}"}

@timed_step("search_courses")
def search_courses_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Search for courses using the generated filters and vector search."""
    try:
        print(f"🔎 Searching courses with filters: {state['filters']}")
        
        # Get conversation history for context
        history = state.get("conversation_history", [])
        
        # Prepare conversation context (last 6 exchanges for context)
        conversation_context = generate_conversation_context(history, max_messages=6)
        
        # Use the filters from the previous node
        course_results = query_courses_with_filters(
            state['user_query'], 
            filters=state['filters'], 
            k=8,
            conversation_context=conversation_context
        )
        
        # Convert to JSON string for the conversational agent
        course_info_json = json.dumps(course_results, indent=2)
        
        print(f"✅ Found {len(course_results)} courses")
        return {**state, "course_results": course_results, "course_info_json": course_info_json, "error": ""}
        
    except Exception as e:
        print(f"❌ Error searching courses: {e}")
        return {**state, "course_results": [], "course_info_json": "[]", "error": f"Failed to search courses: {str(e)}"}

@timed_step("generate_response")
def generate_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate the final response using the conversational agent template with memory."""
    try:
        if state.get("error"):
            return {**state, "response": f"I encountered an error: {state['error']}. Please try rephrasing your query."}
        
        # Get conversation history and user profile
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 6 exchanges for context)
        conversation_context = generate_conversation_context(history, max_messages=6)
        
        prompt_template = ChatPromptTemplate.from_template(prompt_manager.get_prompt("mixed_response"))
        # Choose prompt template based on intent
        
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
