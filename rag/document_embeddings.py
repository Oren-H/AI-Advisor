"""
Course Database Manager

This script provides a unified interface for building and querying the course vector database.
It automatically detects if the database exists and either loads it for querying or builds it if needed.
"""

from database_utils import database_exists, print_database_status
from build_vector_db import build_vector_database
from query_courses import query_courses

def main():
    """
    Main function that either builds the database or allows querying.
    """
    print("🎓 Columbia Courses Vector Database Manager")
    print("=" * 50)
    
    # Check database status
    print_database_status()
    print()
    
    if database_exists():
        print("Database exists! You can now query courses.")
        print("Example queries:")
        print("  - 'I want a Calculus course in the math department'")
        print("  - 'Show me computer science courses with 3 credits'")
        print("  - 'Find courses taught by John Smith'")
        print("  - 'What machine learning courses are available?'")
        print()
        
        # Example query
        query = "I want a Calculus course in the math department that starts after 4pm"
        print(f"Running example query: '{query}'")
        results = query_courses(query)
        
    else:
        print("Database doesn't exist. Building it now...")
        print("(This may take a few minutes depending on your data size)")
        print()
        
        try:
            build_vector_database()
            print("\n✅ Database built successfully!")
            print("You can now run queries using query_courses.py")
            
        except Exception as e:
            print(f"❌ Error building database: {e}")

if __name__ == "__main__":
    main()
