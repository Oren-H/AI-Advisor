
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain.tools import tool
from langchain.chat_models import init_chat_model

from agent.db_querying.query_courses_from_filter import query_courses_with_filters
from agent.db_querying.generate_filters import generate_filters_from_prompt

from langchain.messages import SystemMessage
from langchain.messages import HumanMessage
from pydantic import BaseModel

from langgraph.checkpoint.memory import MemorySaver 
from langgraph.graph import StateGraph, START, END

from major_scraping.bulletin_db import create_chroma_db, load_documents_with_cache

from typing import Dict, List, Any, TypedDict, Annotated, Literal, Optional
from operator import add
from pydantic import Field

import os 
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import create_agent

from langchain_anthropic import ChatAnthropic

from langchain_community.document_loaders import PyPDFLoader

# @node 
# def profile_update(state: CourseAdvisorState) -> CourseAdvisorState:
#     """Update the user's profile based on the user's query."""
#     pass


from typing import Dict, List, Any, TypedDict, Annotated

import conversation_utils as conv_utils
from agent.llm_manager import LLMManager

class IntentRoute(BaseModel):
    """Intent route"""
    intent: Optional[Literal["major_search", "course_search", "general"]] = Field(default="general", 
        description="Figuring out the intent of the user query") 
    reasoning: Optional[str] = Field(default="", description="Brief explanation of why this intent was chosen") 

class UserProfile(BaseModel):
    """User profile"""
    department_of_major: Optional[str] = Field(default="")
    major: Optional[str] = Field(default="")
    completed_courses: Optional[List[str]] = Field(default_factory=list)
    career_goals: Optional[List[str]] = Field(default_factory=list)
    semester: Optional[str] = Field(default="")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)

# Define the state schema
class CourseAdvisorState(BaseModel):
    """State schema for the course advisor agent."""
    # Input/OutpuT
    user_query: str = "" # user gives 
    agent_response: str = "" # agent response 
    messages: List[str] = Field(default_factory=list)
    llm_calls: int = 0
    llm_optimized_query: str = ""
    course_results: Optional[List[Dict[str, Any]]] = None
    major_requirements: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_profile: Optional[UserProfile] = None
    intent: Optional[IntentRoute] = None

openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

llm_manager = LLMManager()
intent_classifier = llm_manager.get_llm(model_provider="openai", model="gpt-4o-mini", 
    temperature=0.2, use_structured_output=True, structured_output_class=IntentRoute)

summarizing_llm = llm_manager.get_llm(model_provider="openai", model="gpt-4o-mini", temperature=0.8)

reasoning_llm = llm_manager.get_llm(model_provider="anthropic", model="claude-sonnet-4-5-20250929", temperature=0.8)


bulletin_db = None

# node
def intent_decision(state: CourseAdvisorState):
    """Classify user intent"""
    try:
        route_result = intent_classifier.invoke(
            [
                SystemMessage(
                    content=f"""
        You are an intent classifier for a university course advisor system.
        Current user query: {state.user_query}
        Classify the intent as ONE of:
        1. "major_search" - User wants help planning their major, understanding requirements, or creating a course schedule
        2. "course_search" - User wants to search for specific courses or get course recommendations
        3. "general" - Anything else not covered by the other intents"""
                ),
                HumanMessage(content=state.user_query),
            ]
        )

        print(f"Intent classified: {route_result.intent}")
        print(f"Reasoning: {route_result.reasoning}")
        return {"intent": route_result, "llm_calls": state.llm_calls + 1}
    except Exception as e:
        print(f"Error in intent_decision: {e}")
        return {"intent": IntentRoute(intent="general", reasoning=str(e)), "llm_calls": state.llm_calls + 1}

# node
def course_search(state: CourseAdvisorState, k: int = 33):
    """Generate metadata filters from user query using the existing generate_filters module."""
    try:
        history = state.messages
        conversation_context = conv_utils.generate_conversation_context(history, max_messages=6)

        # to-do: add user_profile to the query to include it in the filters 
        filters, llm_optimized_query, unique_courses_only = generate_filters_from_prompt(state.user_query, conversation_context)
        course_results = query_courses_with_filters(
            llm_optimized_query,
            filters=filters,
            k=k,
            conversation_context=conversation_context,
            unique_courses_only=unique_courses_only
        )

        return {
            "course_results": course_results,
            "llm_optimized_query": llm_optimized_query,
            "llm_calls": state.llm_calls + 1
        }
    except Exception as e:
        print(f"Error in course_search: {e}")
        return {"course_results": [], "llm_calls": state.llm_calls + 1}

# node
def course_response(state: CourseAdvisorState):
    """Generate a response to the user's query about their courses."""
    try:
        history = state.messages
        conversation_context = conv_utils.generate_conversation_context(history, max_messages=6)

        prompt = f"""
        Based on the the user's query and the course search results, generate a response to the user.
        Most recent user query: {state.user_query}
        Course search results: {state.course_results}
        
        Make sure that the classes are relevant to the user's career goals and preferences.
        Career goals of the user: {state.user_profile.career_goals}
        Preferences of the user: {state.user_profile.preferences}
        Conversation context: {conversation_context}
        
        Consider their user profile for preferences and goals: {state.user_profile}
        Generate a response to the user that is helpful and informative.
        """

        # streaming response?
        response = summarizing_llm.invoke([
                SystemMessage(content=prompt),
                HumanMessage(content=state.user_query),
            ]
        )
        return {"agent_response": response.content, "llm_calls": state.llm_calls + 1}
    except Exception as e:
        print(f"Error in course_response: {e}")
        return {"agent_response": "I'm sorry, I'm having trouble generating a response. Please try again.", "llm_calls": state.llm_calls + 1}

# node
def major_search(state: CourseAdvisorState):
    """Get the major requirements from the user's profile or plan a major course schedule."""
    global bulletin_db
    try:
        persist_dir = "major_scraping/chroma_db/"
        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            print("Loading existing vector database")
            embeddings = OpenAIEmbeddings()
            bulletin_db = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings
            )
            print("Loaded database")
        else:
            print("Creating new vector database...")
            bulletin_db = create_chroma_db()
    except Exception as e:
        print(f"Error in major_search db loading: {e}")
        return {"major_requirements": "I'm sorry, I'm having trouble getting the major requirements. Please try again.", "llm_calls": state.llm_calls + 1}

    try:
        major = state.user_profile.major if state.user_profile else "Computer Science"
        print(f"Major: {major}")

        # Get major requirements directly from the bulletin database
        requirements = get_major_requirements(major=major,k=5)

        # Use LLM to format the response based on user query
        response = reasoning_llm.invoke([
            SystemMessage(content=f"""
            You are an expert academic advisor for Columbia Engineering.
            Based on the major requirements below, answer the user's question.
            Always cite the source (page numbers) when referencing requirements.
            If you can't find specific information, say so clearly.

            Major Requirements:
            {requirements}
            """),
            HumanMessage(content=f"User query: {state.user_query}")
        ])

        print(f"Major search response: {response.content}")

        return {"major_requirements": response.content, "llm_calls": state.llm_calls + 2}
    except Exception as e:
        print(f"Error in major_search: {e}")
        return {"major_requirements": "I'm sorry, I'm having trouble getting the major requirements. Please try again.", "llm_calls": state.llm_calls + 1}

# Define page mappings for major requirements (deterministic)
# TODO: Update these page numbers based on your actual bulletin PDF
MAJOR_PAGE_MAPPINGS = {
    "Computer Science": [166,167,168]
}

def get_major_requirements(major: str, k: int = 5) -> str:
    """Get the major requirements from the bulletin using deterministic page mapping."""

    try:
        # First, try to get pages from the deterministic mapping
        page_numbers = MAJOR_PAGE_MAPPINGS.get(major)
        print(f"Retrieving pages {page_numbers} for {major}")

        # Retrieve documents for the specified pages
        context_chunks = []
        cache_path = "app/graph/__pklcache__/bulletin_doc_cache.pkl"
        bulletin_file_path = "major_scraping/Bulletin_2025-2026_PDF_with_cover_page_.pdf"
        documents = load_documents_with_cache(bulletin_file_path, cache_path)
        for page_num in page_numbers:
            try:
                
                page_doc = documents[page_num-1]
                if page_doc:
                    context_chunks.append(
                        f"Page {page_num}:\n{page_doc.page_content}"
                    )
            except Exception as e:
                print(f"Error retrieving page {page_num}: {e}")
                continue

        if not context_chunks:
            return f"No content found for '{major}' on specified pages."

        context = "\n\n---\n\n".join(context_chunks)

        print(f"Major context: {context}")

        print(f"Retrieved {len(context_chunks)} pages for {major}")

        return (
            f"Major requirements for '{major}':\n\n"
            f"{context}\n\n"
            f"Sources: Pages {sorted(page_numbers)}"
        )
    except Exception as e:
        print(f"Error in get_major_requirements: {e}")
        return "I'm sorry, I'm having trouble getting the major requirements. Please try again."

@tool
def plan_major(state: CourseAdvisorState) -> str:
    """Plan a major course schedule."""
    # to be implemented 
    return "Plan a major course schedule."

# node
def general_response(state: CourseAdvisorState):
    """Generate a response to the user's query."""
    try:
        return {"agent_response": f"Thanks for your query: {state.user_query}", "llm_calls": state.llm_calls + 1}
    except Exception as e:
        print(f"Error in general_response: {e}")
        return {"agent_response": "I'm sorry, I'm having trouble generating a response. Please try again.", "llm_calls": state.llm_calls + 1}

def get_intent(state: CourseAdvisorState) -> str:
    """Route based on intent"""
    return state.intent.intent if state.intent else "general"

workflow = StateGraph(CourseAdvisorState)

workflow.add_node("intent_decision", intent_decision)
workflow.add_node("course_search", course_search)
workflow.add_node("major_search", major_search)
workflow.add_node("course_response", course_response)
workflow.add_node("general_response", general_response)

workflow.add_edge(START, "intent_decision")
workflow.add_conditional_edges(
    "intent_decision",
    get_intent,
    {
        "major_search": "major_search",
        "course_search": "course_search", 
        "general": "general_response"
    }
)
workflow.add_edge("course_search", "course_response")
workflow.add_edge("course_response", END)
workflow.add_edge("major_search", END)
workflow.add_edge("general_response", END)

graph = workflow.compile(checkpointer=MemorySaver())

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "test-thread-1"}}  # Enables persistence/checkpointing
    initial_state = {
        "user_query": "What are the elective requirements for the CS major?",
        "user_profile": {"major": "Computer Science", "career_goals": ["Machine Learning related jobs"]},
        "messages": [],
        "llm_calls": 0
    }

    # result = graph.invoke(initial_state, config)
    # print(result["intent"])  # Should show "course_search" or "major_search"
    # print(result.get("course_results", []))

    # Streaming (watch execution step-by-step)
    for chunk in graph.stream(initial_state, config, stream_mode="values"):
        print(chunk)  # Shows state after each node)

    """
    caching with anthropic 
    parallelization 
    """
    