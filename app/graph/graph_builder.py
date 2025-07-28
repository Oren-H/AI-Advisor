from langgraph.graph import StateGraph, START, END
from app.graph.state_schema import CourseAdvisorState
from app.graph.nodes import (
    intent_classification_node,
    generate_filters_node,
    search_courses_node,
    generate_response_node,
    advisory_response_node,
    route_by_intent
)
from app.graph.memory_nodes import (
    update_memory_node,
    finalize_memory_node
)

def create_course_advisor_graph():
    """Create the LangGraph for the course advisor."""
    
    # Create the workflow
    workflow = StateGraph(CourseAdvisorState)
    
    # Add nodes
    workflow.add_node("update_memory", update_memory_node)
    workflow.add_node("intent_classification", intent_classification_node)
    workflow.add_node("generate_filters", generate_filters_node)
    workflow.add_node("search_courses", search_courses_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("advisory_response", advisory_response_node)
    workflow.add_node("finalize_memory", finalize_memory_node)
    
    # Add edges with conditional routing
    workflow.add_edge(START, "update_memory")
    workflow.add_edge("update_memory", "intent_classification")
    
    # Conditional routing based on intent
    workflow.add_conditional_edges(
        "intent_classification",
        route_by_intent,
        {
            "advisory_response": "advisory_response",
            "generate_filters": "generate_filters"
        }
    )
    
    # Course search path
    workflow.add_edge("generate_filters", "search_courses")
    workflow.add_edge("search_courses", "generate_response")
    
    # Finalize memory before ending
    workflow.add_edge("generate_response", "finalize_memory")
    workflow.add_edge("advisory_response", "finalize_memory")
    
    # End points
    workflow.add_edge("finalize_memory", END)
    
    # Compile the graph
    return workflow.compile() 