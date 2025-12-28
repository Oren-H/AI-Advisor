"""
Graph-based course advisor using LangGraph.

This module provides a graph-based approach to course advising using LangGraph,
with nodes for intent classification, filter generation, course search, and response generation.
"""

from agent.graph.graph_builder import create_course_advisor_graph
from agent.graph.memory_nodes import update_memory_node, finalize_memory_node
from agent.graph.nodes import (
    intent_classification_node,
    generate_filters_node,
    search_courses_node,
    generate_response_node,
    advisory_response_node,
    route_by_intent
)
from agent.graph.state_schema import CourseAdvisorState

__all__ = [
    'create_course_advisor_graph',
    'update_memory_node',
    'finalize_memory_node',
    'intent_classification_node',
    'generate_filters_node',
    'search_courses_node',
    'generate_response_node',
    'advisory_response_node',
    'route_by_intent',
    'CourseAdvisorState',
] 