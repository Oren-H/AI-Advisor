#!/usr/bin/env python3
"""
Test script to verify that all absolute imports are working correctly.
"""

def test_imports():
    """Test all the main imports to ensure they work with absolute paths."""
    
    print("Testing absolute imports...")
    
    try:
        # Test app imports
        from app.db_querying.department_codes import DEPARTMENT_CODES
        print("✅ app.db_querying.department_codes import successful")
    except ImportError as e:
        print(f"❌ app.db_querying.department_codes import failed: {e}")
    
    try:
        # Test scripts import
        from scripts.graph_runner import run_course_advisor
        print("✅ scripts.graph_runner import successful")
    except ImportError as e:
        print(f"❌ scripts.graph_runner import failed: {e}")
    
    try:
        # Test app.graph imports
        from app.graph.state_schema import CourseAdvisorState
        print("✅ app.graph.state_schema import successful")
    except ImportError as e:
        print(f"❌ app.graph.state_schema import failed: {e}")
    
    try:
        # Test app.db_building imports
        from app.db_building.database_utils import database_exists
        print("✅ app.db_building.database_utils import successful")
    except ImportError as e:
        print(f"❌ app.db_building.database_utils import failed: {e}")
    
    print("\nImport structure test completed!")

if __name__ == "__main__":
    test_imports() 