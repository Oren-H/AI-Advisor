from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
import os
from app.db_building.database_utils import load_vector_database
from app.db_querying.generate_filters import generate_filters_from_prompt

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
        # Get the correct path to the database (at the root level)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels: rag/agent/ -> rag/ -> root, then add chroma_db
        chroma_db_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "chroma_db")
        vectordb = load_vector_database(chroma_db_path)
        
        # Perform semantic search with filters
        print(f"Performing semantic search: {query}")
        results = vectordb.similarity_search(query, k=k, filter=filters)
        # results = [d for d in raw if metadata_matches_filters(d.metadata, filters)]

        # Display results
        print(f"\nFound {len(results)} relevant course{'s' if len(results) != 1 else ''}:")
        
        # Convert Document objects to dictionaries for JSON serialization
        course_dicts = []
        for i, doc in enumerate(results, 1):
            course_dict = {
                "course_title": doc.metadata.get('course_title', None),
                "course_code": doc.metadata.get('course_code', None),
                "department": doc.metadata.get('department', None),
                "department_code": doc.metadata.get('department_code', None),
                "points": doc.metadata.get('points', None),
                "instructor": doc.metadata.get('instructor', None),
                "scheduled_time_start": doc.metadata.get('scheduled_time_start', None),
                "scheduled_time_end": doc.metadata.get('scheduled_time_end', None),
                "scheduled_days": doc.metadata.get('scheduled_days', None),
                "type": doc.metadata.get('type', None),
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            }
            course_dicts.append(course_dict)
            
            print(f"\n{i}. {course_dict['course_title']} ({course_dict['course_code']})")
            print(f"   Department: {course_dict['department']}")
            print(f"   Credits: {course_dict['points']}")
            print(f"   Instructor: {course_dict['instructor']}")
            print(f"   Times: {course_dict['scheduled_time_start']} - {course_dict['scheduled_time_end']}")
            print(f"   Days: {course_dict['scheduled_days']}")
            print(f"   Type: {course_dict['type']}")
            print(f"   Content: {course_dict['content'][:200]}...")
        
        return course_dicts
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

if __name__ == "__main__":
    # Example queries
    queries = [
        "Find me an EE class that works with computer architecture"
    ]
    
    for query in queries:
        print("=" * 60)
        filters = generate_filters_from_prompt(query)
        print(filters)
        results = query_courses_with_filters(query, filters=filters, k=5)
        print(results)
   