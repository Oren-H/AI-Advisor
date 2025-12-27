import os
import json
from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
import logging
import requests
from bs4 import BeautifulSoup

# Import our existing modules using absolute imports
from app.db_querying.generate_filters import generate_filters_from_prompt
from app.db_querying.query_courses_from_filter import query_courses_with_filters
from major_scraping.generate_major_context import generate_major_context
from app.graph.state_schema import CourseAdvisorState
from app.graph.conversation_utils import generate_conversation_context
from app.prompt_manager import prompt_manager
from app.llm_manager import llm_manager
from app.utils.timed_step import timed_step

@timed_step("intent_classification")
def intent_classification_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Classify the user's intent based on their query and conversation history."""
    try:
        print(f"🧠 Classifying intent for query: {state['user_query']}")
        
        # Get conversation history for context
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 4 exchanges for context)
        conversation_context = generate_conversation_context(history, max_messages=4)
        
        # Create a prompt for intent classification with memory
        intent_prompt = ChatPromptTemplate.from_template(prompt_manager.get_prompt("intent_classification"))
        
        # Get shared LLM instance
        llm = llm_manager.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.1)
        
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
        if intent not in ["SPECIFIC", "ADVISORY", "MIXED", "MAJOR"]:
            # Default to mixed if classification is unclear
            intent = "MIXED"
        
        print(f"✅ Classified intent as: {intent}")
        return {**state, "intent": intent.lower(), "error": ""}
        
    except Exception as e:
        print(f"❌ Error classifying intent: {e}")
        return {**state, "intent": "mixed", "error": f"Failed to classify intent: {str(e)}"}

@timed_step("generate_course_filters")
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

@timed_step("advisory_response")
def advisory_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate advisory response without course search, using conversation memory."""
    try:
        print(f"💡 Generating advisory response for intent: {state['intent']}")
        
        # Get conversation history and user profile
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 6 exchanges for context)
        conversation_context = generate_conversation_context(history, max_messages=6)
        
        # Create an advisory-focused prompt template with memory
        advisory_prompt = ChatPromptTemplate.from_template(prompt_manager.get_prompt("advisory_response"))
        
        # Get shared LLM instance
        llm = llm_manager.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.7)
        
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

@timed_step("generate_response")
def generate_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate the final response using the conversational agent template with memory."""
    try:
        if state.get("error"):
            return {**state, "response": f"I encountered an error: {state['error']}. Please try rephrasing your query."}
        
        if not state.get("course_results") and not state.get("course_plan"):
            return {**state, "response": "I couldn't find any courses matching your criteria. Please try broadening your search or rephrasing your query."}
        
        if state.get("intent") == "major":
            return {**state, "response": state.get("course_plan", "")}
        
        # Get conversation history and user profile
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 6 exchanges for context)
        conversation_context = generate_conversation_context(history, max_messages=6)
        
        # Choose prompt template based on intent
        if state.get("intent") == "mixed":
            # Mixed intent: combine advisory guidance with course recommendations
            prompt_template = ChatPromptTemplate.from_template(prompt_manager.get_prompt("mixed_response"))
        else:
            # Specific intent: focus on course recommendations
            prompt_template = ChatPromptTemplate.from_template(prompt_manager.get_prompt("specific_response"))
        
        # Get shared LLM instance
        llm = llm_manager.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.7)
        
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

@timed_step("generate_major_context")
def major_context_node(state: CourseAdvisorState) -> CourseAdvisorState:
    try: 
        print(f"💡 Generating major plan for user: {state.get('user_profile', {})}")

        # TODO: Remove hardcoded profile once user profile system is implemented
        # For now, use hardcoded test profile
        test_profile = {
            "department_of_major": "MATH",
            "major": "Major in Mathematics", 
            "completed_courses": ["MATH UN1101", "MATH UN1102"],
            "years_left": 4,
            "career_goals": ["Graduate School", "Pure Mathematics"]
        }
        
        department_of_major = test_profile.get("department_of_major", "")
        major = test_profile.get("major", "")
        
        print(f"🧪 Using test profile: {department_of_major} - {major}")
        major_context = generate_major_context(department_of_major, major)

        return {
            **state,
            "user_profile": test_profile,  # Add test profile to state
            "major_context": major_context,
            "error": ""
        }
    except Exception as e:
        print(f"❌ Error generating major context: {e}")
        return {**state, "error": f"Failed to generate major context: {str(e)}"}

@timed_step("plan_major")
def plan_major_node(state: CourseAdvisorState) -> CourseAdvisorState:
    try:
        if not state.get("major_context"):
            return {**state, "error": "No major context provided"}
        
        print(f"💡 Planning major from context for user: {state['user_profile']}")
        
        user_profile = state.get("user_profile", {})
        completed_courses = user_profile.get("completed_courses", [])
        major = user_profile.get("major", "")
        years_left = user_profile.get("years_left", 4)
        major_context = state.get("major_context", {})

        # Create a prompt for the planner
        major_plan_prompt = ChatPromptTemplate.from_template(prompt_manager.get_prompt("plan_major"))
        llm = llm_manager.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.8)
        
        # Create the chain
        chain = major_plan_prompt | llm
        
        # Generate response
        response = chain.invoke({
            "user_profile": json.dumps(user_profile, indent=2),
            "major_context": json.dumps(major_context, indent=2),
            "major": major,
            "completed_courses": completed_courses,
            "years_left": years_left,
        })
        print(f"✅ Course plan: {response.content}")
        return {**state, "course_plan": response.content, "error": ""}
    except Exception as e:
        print(f"❌ Error planning major from HTML: {e}")
        return {**state, "error": f"Failed to plan major from HTML: {str(e)}"}

@timed_step("route_by_intent")
def route_by_intent(state: CourseAdvisorState) -> str:
    """Route to different paths based on the user's intent."""
    intent = state.get("intent", "mixed")
    
    if intent == "advisory":
        return "advisory_response"
    elif intent == "specific":
        return "generate_filters"
    elif intent == "major":
        return "generate_major_context"
    else:  # mixed
        return "generate_filters" 
