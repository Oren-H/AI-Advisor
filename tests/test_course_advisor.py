#!/usr/bin/env python3
"""
Test script for the LangGraph-based course advisor.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from course_advisor_graph import run_course_advisor

def test_course_advisor():
    """Test the course advisor with sample queries."""
    
    test_queries = [
        "Find me computer science courses with 3 credits",
        "Show me machine learning courses offered on Tuesday",
        "What math courses are available for beginners?",
        "Find courses in the psychology department"
    ]
    
    print("🧪 Testing Course Advisor Integration")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 30)
        
        try:
            response = run_course_advisor(query)
            print(f"✅ Response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_course_advisor() 