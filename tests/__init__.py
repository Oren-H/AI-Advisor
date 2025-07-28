"""
Test suite for the AI Course Advisor.

This module contains all test files for the course advisor application.
"""

from tests.test_course_advisor import test_course_advisor
from tests.test_functions import test_functions
from tests.test_modular_structure import test_modular_structure
from tests.scraper_tester import test_scraper

__all__ = [
    'test_course_advisor',
    'test_functions', 
    'test_modular_structure',
    'test_scraper'
] 