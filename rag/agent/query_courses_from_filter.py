from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_utils import load_vector_database
from generate_filters import generate_filters_from_prompt

def query_courses_with_filters(query: str, filters: dict = None, k: int = 1):
    """
    Query the course database with filters and semantic search.
    
    Args:
        query (str): Natural language query about courses
        filters (dict): Metadata filters to apply (from generate_filters)
        k (int): Number of results to return
    
    Returns:
        List of relevant course documents
    """
    try:
        vectordb = load_vector_database()
        
        # Perform semantic search with filters
        print(f"Performing semantic search: {query}")
        results = vectordb.similarity_search(query, k=k, filter=filters)
        # results = [d for d in raw if metadata_matches_filters(d.metadata, filters)]

        # Display results
        print(f"\nFound {len(results)} relevant course{'s' if len(results) != 1 else ''}:")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc.metadata.get('course_title', 'N/A')} ({doc.metadata.get('course_code', 'N/A')})")
            print(f"   Department: {doc.metadata.get('dept', 'N/A')}")
            print(f"   Credits: {doc.metadata.get('credits', 'N/A')}")
            print(f"   Instructor: {doc.metadata.get('instructor', 'N/A')}")
            print(f"   Times: {doc.metadata.get('time_starting', 'N/A')} - {doc.metadata.get('time_ending', 'N/A')}")
            print(f"   Days: {doc.metadata.get('days_offered', 'N/A')}")
            print(f"   Enrolled: {doc.metadata.get('enrolled', 'N/A')} / {doc.metadata.get('max_enrollment', 'N/A')}")
            print(f"   Currently Offered: {doc.metadata.get('offered', 'N/A')}")
            print(f"   Content: {doc.page_content[:200]}...")
        
        return results
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

if __name__ == "__main__":
    # Example queries
    queries = [
        "Show me computer science courses about machine learning that are three credits"
    ]
    
    for query in queries:
        print("=" * 60)
        filters = generate_filters_from_prompt(query)
        print(filters)
        results = query_courses_with_filters(query, filters=filters, k=5)
        