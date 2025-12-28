"""
Database building utilities for the course advisor.

This module provides utilities for building and managing the vector database
used for course search and recommendations.
"""

from agent.db_building.build_vector_db import build_vector_database
from agent.db_building.database_utils import (
    load_vector_database,
    database_exists,
    get_database_info,
    print_database_status
)

__all__ = [
    'build_vector_database',
    'load_vector_database',
    'database_exists',
    'get_database_info',
    'print_database_status'
] 