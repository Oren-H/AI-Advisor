"""
This is a simpler graph builder that only includes the nodes that are necessary for the course advisor.

START - update_memory (get rid of user profile feature?)
update_memory - filter_generation
filter_generation - search_courses
search_courses - generate_response
generate_response - finalize_memory
finalize_memory - END
"""

from langgraph.graph import StateGraph, START, END
from agent.graph.state_schema import CourseAdvisorState
from agent.graph.simplified_nodes import (
    generate_filters_node,
    search_courses_node,
    generate_response_node,
)
from agent.graph.memory_nodes import (
    update_memory_node,
    finalize_memory_node
)

def create_simplified_course_advisor_graph():
    """Create the LangGraph for the course advisor."""
    
    # Create the workflow
    workflow = StateGraph(CourseAdvisorState)
    
    # Add nodes
    workflow.add_node("update_memory", update_memory_node)
    workflow.add_node("generate_filters", generate_filters_node)
    workflow.add_node("search_courses", search_courses_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("finalize_memory", finalize_memory_node)
    
    # Add edges with conditional routing
    workflow.add_edge(START, "update_memory")
    workflow.add_edge("update_memory", "generate_filters")
    workflow.add_edge("generate_filters", "search_courses")
    workflow.add_edge("search_courses", "generate_response")
    workflow.add_edge("generate_response", "finalize_memory")
    workflow.add_edge("finalize_memory", END)
    
    return workflow.compile()
