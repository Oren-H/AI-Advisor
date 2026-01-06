
import sys
from pathlib import Path

# Get project root and add to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from project root
from dotenv import load_dotenv

load_dotenv(project_root / ".env")

import logging
import os
from typing import Any, Dict, List, Literal

logger = logging.getLogger("tools")

from agent.database_cache import db_cache
from agent.db_querying.generate_course_filters import generate_filters_from_prompt
from agent.db_querying.query_courses_from_filter import query_courses_with_filters
from agent.graph.majors_summary import requirements
from agent.graph.school_requirements import school_requirements
from agent.prompt_manager import prompt_manager

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentState,
    ClearToolUsesEdit,
    ContextEditingMiddleware,
    ToolCallLimitMiddleware,
)
from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime, tool
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from pydantic import BaseModel, Field

openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

class UserProfile(AgentState):
    """User profile"""
    user_id: str
    name: str
    school: str
    department_of_major: str 
    major: str
    completed_courses: List[str]
    semester: int # = Field(description="The semester the user is in out of 8 semesters")
    career_goals: List[str] # = Field(default_factory=list)
    preferences: List[str] # = Field(default_factory=dict)


@tool(description="Get the user's profile")
def get_user_profile(runtime: ToolRuntime[None, UserProfile]) -> str:
    """Get complete user profile."""
    try:
        logger.info("Tool call: get_user_profile")
        state = runtime.state
        profile = f"""
        **USER PROFILE**
        ID: {state.get('user_id')}
        Name: {state.get('name')}
        School: {state.get('school')}
        Major: {state.get('major')} ({state.get('department_of_major')})
        Semester: {state.get('semester')}/8
        Completed: {state.get('completed_courses', [])}
        Goals: {state.get('career_goals', [])}
        Preferences: {state.get('preferences', {})}
        """
        logger.info(f"Retrieved user profile for {state.get('user_id')}")
        return profile.strip()
    except Exception as e:
        logger.error(f"Error in get_user_profile: {e}", exc_info=True)
        return "I'm sorry, I'm having trouble getting the user profile."

class SearchCoursesInput(BaseModel):
    query: str = Field(description="Natural language query like 'machine learning classes on Mondays'")
    limit: int = Field(description="Number of courses to return", default=3) 
    unique_courses_flag: bool = Field(description="Flag to indicate if unique courses should be returned", default=True)

@tool(description="Vector search for courses based on the user's query that creates filters")
def search_courses(input: SearchCoursesInput) -> Dict[str, Any]:
    """Retrieve the course context from the database using the query and limit."""
    try:
        logger.info(f"Tool call: search_courses - query: '{input.query}', limit: {input.limit}")

        filters = generate_filters_from_prompt(input.query)
        logger.info(f"Generated filters: {filters}")

        course_results = query_courses_with_filters(
            query=input.query,
            filters=filters,
            k=input.limit,
            # conversation_context="",
            unique_courses_only=input.unique_courses_flag
        )

        logger.info(f"Found {len(course_results)} courses")
        return {"course_titles": [course["course_title"] for course in course_results], 
                "total_count": len(course_results),
                "course_info": course_results}
    except Exception as e:
        logger.error(f"Error in search_courses: {e}", exc_info=True)
        return "I'm sorry, I'm having trouble searching the courses. Please try again."

@tool(description="Lookup a course by course code")
def lookup_course(course_code: str) -> Dict[str, Any]:
    """Retrieve the course context from the database."""
    try:
        logger.info(f"Tool call: lookup_course - code: {course_code}")
        courses_df = db_cache.get_course_df()
        course_results = courses_df[courses_df["course_code"] == course_code].to_dict(orient="records")
        logger.info(f"Found {len(course_results)} courses for code: {course_code}")
        return {"total_count": len(course_results),
                "course_info": course_results}
    except Exception as e:
        logger.error(f"Error in lookup_course: {e}", exc_info=True)
        return "I'm sorry, I'm having trouble looking up the course. Please try again."


class SearchBulletinInput(BaseModel):
    agentic_query: str = Field(description="A query generated by the agent that considers user profile and preferences")
    limit: int = Field(description="Number of results to return", default=3)

@tool(description="Vector search for bulletin based on query")
def search_bulletin(input: SearchBulletinInput, crush_flag = True) -> Dict[str, Any]:
    """Search the major requirements"""
    try:
        bulletin_vector_db = db_cache.get_bulletin_db()
    except Exception as e:
        logger.error(f"Error loading bulletin DB: {e}", exc_info=True)
        return {"results": [], "error": str(e)}

    try:
        # writer = get_stream_writer()
        # writer(f"Tool call: search_bulletin")
        # writer(f"Searching up bulletin with the query: {input.agentic_query}")
        logger.info(f"Tool call: search_bulletin - query: '{input.agentic_query}', limit: {input.limit}")
        # Use the bulletin_vector_db already loaded above
        docs = bulletin_vector_db.similarity_search(input.agentic_query, k=input.limit)  # type: ignore[union-attr]
        results = [{"page_content": d.page_content, "metadata": d.metadata} for d in docs]
        # writer(f"Found {len(results)} results")
        logger.info(f"Found {len(results)} bulletin results")
        return {"results": results}
    except Exception as e:
        logger.error(f"Error in search_bulletin: {e}", exc_info=True)
        return "I'm sorry, I'm having trouble searching the bulletin. Please try again."


MAJOR_PAGE_MAPPINGS = {
    "applied mathematics": [66,67],
    "computer science": [166,167,168,169], 
    "electrical engineering": [220,221,222,223,224,225,226]
}

@tool(description="Lookup major requirements from the bulletin (e.g. electrical engineering)")
def lookup_major(major: str) -> str:
    try:
        major = major.lower()
        pages = MAJOR_PAGE_MAPPINGS[major]

        logger.info(f"Tool call: lookup_major - major: {major}")
        
        result = {
            "major_title": major,
            "major_requirements": requirements[major],
            "source": pages
        }
        logger.info(f"Retrieved requirements for {major} from pages {pages}")
        return result
    except Exception as e: 
        logger.error(f"Error in lookup_major: {e}", exc_info=True)
        return "I'm sorry, I'm having trouble getting the major requirements. Please try again."

class SchoolWideRequirementInput(BaseModel):
    # school: str = Field(Literal["SEAS"], description="The school to lookup requirements for")
    query: Literal["nontechnical_requirements", "technical_requirements",
        "course_eligibility_rules", "advanced_placement_and_external_credit"] = Field(description="The school-wide requirement to lookup")

@tool(description="Lookup school-wide requirements from the bulletin")
def lookup_school_wide_requirements(input: SchoolWideRequirementInput) -> str:
    """Lookup school-wide requirements from the school requirements database."""
    try:
        logger.info(f"Tool call: lookup_school_wide_requirements - query: {input.query}")
        result = school_requirements[input.query]
        logger.info(f"Retrieved school requirement: {input.query}")
        return result
    except Exception as e:
        logger.error(f"Error in lookup_school_wide_requirements: {e}", exc_info=True)
        return "I'm sorry, I'm having trouble getting the school-wide requirements. Please try again."

SYSTEM_PROMPT = prompt_manager.get_prompt("agent_system_prompt")

def get_course_advisor_agent():
    """Create and return the course advisor agent configured with tools and memory."""
    # model = ChatAnthropic(
    #     model="claude-sonnet-4-5-20250929",
    #     temperature=0.8,
    #     max_tokens=5000,
    #     timeout=60
    # )
    model = ChatOpenAI(
        model = "gpt-5.2-2025-12-11",
        temperature=0.8,
        max_tokens=5000,
        timeout=120
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
            ContextEditingMiddleware(
            token_count_method="approximate",
            edits=[
                ClearToolUsesEdit(
                    trigger=20000,
                    keep=15,
                    clear_tool_inputs=False, 
                    exclude_tools=["lookup_major","lookup_school_wide_requirements"]
                )],
            ),
            # global 
            ToolCallLimitMiddleware(
                thread_limit=100, 
                run_limit=50
            ), 
            ToolCallLimitMiddleware(
                tool_name="search_courses",
                thread_limit=15, 
                run_limit=5, 
            ),
            ToolCallLimitMiddleware(
                tool_name="lookup_major",
                thread_limit=2, 
                run_limit=1, 
            ),
            ToolCallLimitMiddleware(
                tool_name="lookup_school_wide_requirements",
                thread_limit=4, 
                run_limit=4, 
            ),
            ToolCallLimitMiddleware(
                tool_name="get_user_profile",
                thread_limit=1, 
                run_limit=1, 
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

    # try:
    #     for chunk in agent.stream(
    #         {
    #             "messages": [HumanMessage(content="Plan my next semester and give me a timetable")],
    #             "user_id": "nl2951@columbia.edu",
    #             "department_of_major": "ELEC",
    #             "major": "Electrical Engineering",
    #             "completed_courses": [],
    #             "semester": 2,
    #             "career_goals": ["FPGA"],
    #             "preferences": [],
    #         },
    #         {
    #             "configurable": {"thread_id": "1"},
    #             "recursion_limit": 50
    #         }, # in production: postgres: https://docs.langchain.com/oss/python/langchain/short-term-memory
    #         stream_mode=["updates", "custom"],
    #     ):
    #         kind, response = chunk 
    #         if kind == "updates" and isinstance(response, dict): 
    #             model = response.get("model", None)
    #             if model:
    #                 messages = model.get("messages", None)
    #                 if messages:
    #                     for msg in messages: 
    #                         content = msg.content
    #                         if content:
    #                             for part in content:
    #                                 if part.get("type") == "text":
    #                                     print(f"\n{part.get('text','')}", end="", flush=True)
    #         if kind == "custom":
    #             print(f"\n{response}")
    # except Exception as e:
    #     print("An exception occurred during streaming:", e)