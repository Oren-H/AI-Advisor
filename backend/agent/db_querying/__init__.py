"""
Database querying utilities for the course advisor.

This module provides utilities for querying the vector database
and generating filters for course searches.
"""

from backend.databases.data.misc.department_codes import dept_codes

from agent.db_querying.generate_course_filters import generate_filters_from_prompt
from agent.db_querying.query_courses_from_filter import query_courses_with_filters

__all__ = [
    'query_courses_with_filters',
    'generate_filters_from_prompt',
    'dept_codes'
] 