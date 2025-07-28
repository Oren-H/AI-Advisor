#!/usr/bin/env python3
"""
Test script to verify the modular structure of the course advisor graph.
"""

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test state schema import
        from state_schema import CourseAdvisorState
        print("✅ state_schema imported successfully")
        
        # Test nodes import
        from nodes import (
            intent_classification_node,
            generate_filters_node,
            search_courses_node,
            generate_response_node,
            advisory_response_node,
            route_by_intent
        )
        print("✅ nodes imported successfully")
        
        # Test memory nodes import
        from memory_nodes import (
            update_memory_node,
            finalize_memory_node
        )
        print("✅ memory_nodes imported successfully")
        
        # Test graph builder import
        from graph_builder import create_course_advisor_graph
        print("✅ graph_builder imported successfully")
        
        # Test graph runner import
        from graph_runner import run_course_advisor, interactive_course_advisor
        print("✅ graph_runner imported successfully")
        
        print("\n🎉 All imports successful! Modular structure is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_state_schema():
    """Test that the state schema can be instantiated."""
    try:
        from state_schema import CourseAdvisorState
        
        # Create a sample state
        sample_state = {
            "user_query": "test query",
            "intent": "mixed",
            "filters": {},
            "course_results": [],
            "course_info_json": "",
            "response": "",
            "error": "",
            "conversation_history": [],
            "user_profile": {}
        }
        
        # This should work without errors
        typed_state: CourseAdvisorState = sample_state
        print("✅ State schema instantiation successful")
        return True
        
    except Exception as e:
        print(f"❌ State schema error: {e}")
        return False

def test_graph_creation():
    """Test that the graph can be created successfully."""
    try:
        from graph_builder import create_course_advisor_graph
        
        # Create the graph
        graph = create_course_advisor_graph()
        print("✅ Graph creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Graph creation error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing modular course advisor structure...\n")
    
    tests = [
        ("Import Test", test_imports),
        ("State Schema Test", test_state_schema),
        ("Graph Creation Test", test_graph_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The modular structure is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 