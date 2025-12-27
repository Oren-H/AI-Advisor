import os
import sys
from pathlib import Path

# Add project root to path for imports when running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from app.db_building.database_utils import load_vector_database
from app.db_querying.generate_filters import generate_filters_from_prompt

def query_courses_with_filters(query: str, filters: dict = None, k: int = 1, conversation_context: str = ""):
    """
    Query the course database with filters and semantic search.
    
    Args:
        query (str): Natural language query about courses
        filters (dict): Metadata filters to apply (from generate_filters)
        k (int): Number of results to return
        conversation_context (str): Optional conversation history for context
    
    Returns:
        List of relevant course documents
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chroma_db_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "course_data", "chroma_db")
        vectordb = load_vector_database(chroma_db_path)
        
        # Enhance the query with conversation context if available
        enhanced_query = query
        if conversation_context:
            enhanced_query = f"Context: {conversation_context}\nQuery: {query}"
        
        # Perform semantic search with filters
        print(f"Performing semantic search: {enhanced_query}")
        # Only pass filters if they're not empty
        if filters:
            results_with_scores = vectordb.similarity_search_with_score(enhanced_query, k=k, filter=filters)
            # Sort by score (lower is better for distance metrics)
            results_with_scores = sorted(results_with_scores, key=lambda x: -x[1])
        else:
            raw_results = vectordb.similarity_search(enhanced_query, k=k)
            # Create tuples with None score for consistency
            results_with_scores = [(doc, None) for doc in raw_results]

        # Display results
        print(f"\nFound {len(results_with_scores)} relevant course{'s' if len(results_with_scores) != 1 else ''}:")

        if(len(results_with_scores)==0):
            print("No results found with filters. Trying without filters.")
            raw_results = vectordb.similarity_search(enhanced_query, k=k)
            results_with_scores = [(doc, None) for doc in raw_results]

        # Convert Document objects to dictionaries for JSON serialization
        course_dicts = []
        for i, (doc, score) in enumerate(results_with_scores, 1):
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
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "similarity_score": score
            }
            course_dicts.append(course_dict)

            score_text = f" (score: {score:.4f})" if score is not None else ""
            print(f"\n{i}. {course_dict['course_title']} ({course_dict['course_code']}){score_text}")
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
        "Find me a IEOR class about optimization after 10am on Tuesday and Thursday "
    ]

    for query in queries:
        filters, text_query = generate_filters_from_prompt(query)
        print(f"Filters: {filters}")
        print(f"Text Query: {text_query}")
        results = query_courses_with_filters(text_query, filters=filters, k=10, conversation_context="")
        print(results)
   