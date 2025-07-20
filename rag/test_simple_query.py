from database_utils import load_vector_database

def test_simple_query():
    """Test a simple query without any filters."""
    try:
        vectordb = load_vector_database()
        
        # Simple semantic search
        print("Testing simple semantic search...")
        results = vectordb.similarity_search_with_relevance_scores(
            query="machine learning",
            k=5
        )
        
        print(f"Found {len(results)} results:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n{i}. Score: {score}")
            print(f"   Title: {doc.metadata.get('course_title', 'N/A')}")
            print(f"   Code: {doc.metadata.get('course_code', 'N/A')}")
            print(f"   Dept: {doc.metadata.get('dept', 'N/A')}")
            print(f"   Content: {doc.page_content[:100]}...")
        
        # Test department filter
        print("\n" + "="*50)
        print("Testing department filter...")
        
        # Get all COMS courses
        all_results = vectordb.similarity_search_with_relevance_scores(
            query="",  # Empty query to get all
            k=100
        )
        
        coms_courses = []
        for doc, score in all_results:
            if doc.metadata.get('dept') == 'COMS':
                coms_courses.append((doc, score))
        
        print(f"Found {len(coms_courses)} COMS courses:")
        for i, (doc, score) in enumerate(coms_courses[:5], 1):
            print(f"\n{i}. Score: {score}")
            print(f"   Title: {doc.metadata.get('course_title', 'N/A')}")
            print(f"   Code: {doc.metadata.get('course_code', 'N/A')}")
            print(f"   Content: {doc.page_content[:100]}...")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_query() 