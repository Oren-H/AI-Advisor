
import sys
from pathlib import Path

# Get project root and add to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from project root
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from langchain.tools import tool
from langchain.chat_models import init_chat_model

from agent.db_querying.query_courses_from_filter import query_courses_with_filters
from agent.db_querying.generate_course_filters import generate_filters_from_prompt

from langchain.messages import SystemMessage
from langchain.messages import HumanMessage

from langchain.agents.middleware import TodoListMiddleware

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from databases.build_bulletin_vector_db import create_chroma_db, load_documents_with_cache
from databases.paths import str_bulletin_db_dir, str_bulletin_cache_path
from agent.database_cache import db_cache

from typing import Dict, List, Any, TypedDict, Annotated, Literal, Optional
from typing import TypedDict, NotRequired, Required, Annotated
from pydantic import BaseModel, Field, ConfigDict

from operator import add

import os
import json
import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import create_agent

from langchain_anthropic import ChatAnthropic

from langchain_community.document_loaders import PyPDFLoader

from langchain_community.retrievers import BM25Retriever

from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit, ToolCallLimitMiddleware



# @node 
# def profile_update(state: CourseAdvisorState) -> CourseAdvisorState:
#     """Update the user's profile based on the user's query."""
#     pass


from typing import Dict, List, Any, TypedDict, Annotated

import agent.graph.conversation_utils as conv_utils
from agent.llm_manager import LLMManager


from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver  

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.agents.middleware import AgentState, before_model, after_model
from typing_extensions import NotRequired
from typing import Any
from langgraph.runtime import Runtime
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime 

openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

class UserProfile(AgentState):
    """User profile"""
    user_id: str
    department_of_major: str 
    major: str
    completed_courses: List[str]
    semester: int # = Field(description="The semester the user is in out of 8 semesters")
    career_goals: List[str] # = Field(default_factory=list)
    preferences: List[str] # = Field(default_factory=dict)
    
class SearchCoursesInput(BaseModel):
    query: str = Field(description="Natural language query like 'machine learning classes on Mondays'")
    limit: int = Field(description="Number of courses to return", default=5) 
    unique_courses_flag: bool = Field(description="Flag to indicate if unique courses should be returned", default=True)

@tool(description="Get the user's profile")
def get_user_profile(runtime: ToolRuntime[None, UserProfile]) -> str:
    """Get complete user profile."""
    state = runtime.state
    profile = f"""
    **USER PROFILE**
    ID: {state.get('user_id')}
    Major: {state.get('major')} ({state.get('department_of_major')})
    Semester: {state.get('semester')}/8
    Completed: {state.get('completed_courses', [])}
    Goals: {state.get('career_goals', [])}
    Preferences: {state.get('preferences', {})}
    """
    return profile.strip()

@tool(description="Vector search for courses based on the user's query that creates filters")
def search_courses(input: SearchCoursesInput) -> Dict[str, Any]:
    """Retrieve the course context from the database using the query and limit."""
    try:
        filters = generate_filters_from_prompt(input.query)
        course_results = query_courses_with_filters(
            query=input.query,
            filters=filters,
            k=input.limit,
            # conversation_context="",
            unique_courses_only=input.unique_courses_flag
        )
        return {"courses": course_results, "total_count": len(course_results)}
    except Exception as e:
        print(f"Error in search_courses: {e}")
        return {"courses": [], "total_count": 0, "error": str(e)}

@tool(description="Lookup a course by course code")
def lookup_course(course_code: str) -> Dict[str, Any]:
    """Retrieve the course context from the database."""
    try:
        courses_df = db_cache.get_course_df()
        course_results = courses_df[courses_df["course_code"] == course_code].to_dict(orient="records") 
        return {"course_results": course_results}
    except Exception as e:
        print(f"Error in lookup_course: {e}")
        return {"course_results": [], "error": str(e)}


class SearchBulletinInput(BaseModel):
    agentic_query: str = Field(description="A query generated by the agent that considers user profile and preferences")
    limit: int = Field(description="Number of results to return", default=3)

@tool(description="Vector search for courses based on query")
def search_bulletin(input: SearchBulletinInput, crush_flag = True) -> Dict[str, Any]:
    """Search the major requirements"""
    try:
        bulletin_vector_db = db_cache.get_bulletin_db()
    except Exception as e: 
        print(f"Error in search_bulletin: {e}")

    try:
        # Use the bulletin_vector_db already loaded above
        docs = bulletin_vector_db.similarity_search(input.agentic_query, k=input.limit)  # type: ignore[union-attr]
        results = [{"page_content": d.page_content, "metadata": d.metadata} for d in docs]
        return {"results": results}
    except Exception as e:
        print(f"Error in search_bulletin: {e}")
        return {"results": [], "error": str(e)}


MAJOR_PAGE_MAPPINGS = {
    "APPLIED MATHEMATICS": [66,67],
    "COMPUTER SCIENCE": [166,167,168,169], 
    "ELECTRICAL ENGINEERING": [220,221,222,223,224,225,226]
}

# class Course(BaseModel):
#     code: str
#     title: str

# class MajorRequirements(BaseModel):
#     major: str
#     degree: str | None = None
#     min_points: int | None = None
#     required_courses: List[Course] = []      # optional detailed list
#     rules: Dict[str, Any] = {}                       # double counting, grades, etc.
#     notes: List[str] = []
#     sources: Dict[str, Any]



@tool(description="Lookup major requirements from the bulletin (e.g. ELECTRICAL ENGINEERING)")
def lookup_major(major: str) -> str:
    try:
        page_numbers = MAJOR_PAGE_MAPPINGS.get(major.upper())
        print(f"Retrieving pages {page_numbers} for {major}")

        context_chunks = []
        documents = db_cache.get_bulletin_documents()

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

        # if major has not been extracted before with an llm, extract it. lets save it in a cache 

        # llm = ChatAnthropic(
        #     model="claude-sonnet-4-5-20250929",
        #     temperature=0.0,
        #     # max_tokens=1200,
        #     timeout=60
        # )

        # system_prompt = SystemMessage(content="""
        # Extract degree requirements for this specific major. 
        # """
        # )
        # llm = llm.with_structured_output(MajorRequirements)
        # major_info = llm.invoke(context)

        # print(f"Major requirements: {major_info}")

        # print(f"Retrieved {len(context_chunks)} pages for {major}")

        return (
            f"Major requirements for '{major}':\n\n"
            f"{context}\n\n"
            f"Sources: Pages {sorted(page_numbers)}"
        )
    except Exception as e:
        print(f"Error in lookup_major: {e}")
        return "I'm sorry, I'm having trouble getting the major requirements. Please try again."

SCHOOL_PAGE_MAPPINGS = {
    "SEAS": [8,9,10,11,12,13,14,15]
}

@tool(description="Lookup school-wide requirements from the bulletin")
def lookup_school_wide_requirements(school: str="SEAS") -> str:
    """Lookup school-wide requirements from the school requirements database."""
    try:
        page_numbers = SCHOOL_PAGE_MAPPINGS.get(school)

        if not page_numbers:
            return f"No page mapping found for school '{school}'. Available schools: {list(SCHOOL_PAGE_MAPPINGS.keys())}"

        print(f"Retrieving pages {page_numbers} for {school}")

        context_chunks = []
        documents = db_cache.get_bulletin_documents()

        for page_num in page_numbers:
            try:
                page_doc = documents[page_num-1]
                if page_doc:
                    context_chunks.append(f"Page {page_num}:\n{page_doc.page_content}")
            except Exception as e:
                print(f"Error retrieving page {page_num}: {e}")
                continue

        if not context_chunks:
            return f"No content found for '{school}' on specified pages."

        context = "\n\n---\n\n".join(context_chunks)
        print(f"Retrieved {len(context_chunks)} pages for {school}")

        return (
            f"School requirements for '{school}':\n\n"
            f"{context}\n\n"
            f"Sources: Pages {sorted(page_numbers)}"
        )
    except Exception as e:
          print(f"Error in lookup_school_requirements: {e}")
          return "I'm sorry, I'm having trouble getting the school requirements. Please try again."

SYSTEM_PROMPT = """
            You are an expert Columbia University course advisor.
            Use the user profile when answering. 
            When planning a major, make sure to check school-wide requirements as well.
            If a user asks to plan next semester, include a schedule where each course has a time slot. 
            If a user asks to plan all of their semesters, do not include times of classes but instead a list of courses in each semester. 
            """
            

def get_course_advisor_agent():
    """Create and return the course advisor agent configured with tools and memory."""
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.8,
        max_tokens=5000,
        timeout=60
    )
    tools = [
        search_courses, 
        lookup_course, 
        search_bulletin, 
        lookup_major, 
        lookup_school_wide_requirements,
        get_user_profile,
    ]
    agent = create_agent(
        model=model, 
        tools=tools,
        state_schema=UserProfile,
        checkpointer=InMemorySaver(),
        middleware=[
            # TodoListMiddleware(),
            # ContextEditingMiddleware(
            # edits=[
            #     ClearToolUsesEdit(
            #         trigger=50000,
            #         keep=2,
            #     )],
            # ),

            # global 
            ToolCallLimitMiddleware(
                thread_limit=20, 
                run_limit=10), 
            ToolCallLimitMiddleware(
                tool_name = "lookup_major",
                thread_limit = 1, 
                run_limit = 1, 
            ),
            ToolCallLimitMiddleware(
                tool_name = "lookup_school_wide_requirements",
                thread_limit = 1, 
                run_limit = 1, 
            ),
        ],
        system_prompt=SYSTEM_PROMPT
    )
    return agent

if __name__ == "__main__":
    agent = get_course_advisor_agent()
    result = agent.invoke(
        {"messages": [HumanMessage(content="Tell me the requirements for electrical engineering")],
        "user_id": "123",
        "department_of_major": "ELEC",
        "major": "Electrical Engineering",
        "completed_courses": [""],
        "semester": 1,
        "career_goals": ["FPGA"],
        "preferences": {"class_time": ""},
        },
        {"configurable": {"thread_id": "1"}}, # in production: postgres: https://docs.langchain.com/oss/python/langchain/short-term-memory
    )


    # for chunk in agent.stream({
    #     "messages": [HumanMessage(content="Help me plan my major in Computer Science")]
    # }, stream_mode="values"):
    #     # Each chunk contains the full state at that point
    #     latest_message = chunk["messages"][-1]
    #     if latest_message.content:
    #         print(f"Agent: {latest_message.content}")
    #     elif latest_message.tool_calls:
    #         print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")

    # print(result)
    # conv_utils.dump_messages_pretty(result["messages"])

    for msg in result["messages"]:
        msg.pretty_print()




