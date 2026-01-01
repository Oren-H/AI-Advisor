import os
import sys
from pathlib import Path

# Add project root to path for imports when running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from agent.db_building.database_utils import load_vector_database
from agent.db_querying.generate_filters import generate_filters_from_prompt
import agent.llm_manager as llm_manager

def query_courses_with_filters(query: str, filters: dict = None, k: int = 10, conversation_context: str = "", unique_courses_only: bool = True):
    """
    Query the course database with filters and semantic search.

    Args:
        query (str): Natural language query about courses
        filters (dict): Metadata filters to apply (from generate_filters)
        k (int): Number of results to return
        conversation_context (str): Optional conversation history for context
        unique_courses_only (bool): If True, return only one section per unique course.
                                     If False, return all matching sections (useful for schedule planning).

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

        # If unique_courses_only, fetch more results to account for deduplication
        # Multiply k by 3 to ensure we get enough unique courses after deduplication
        fetch_k = k * 3 if unique_courses_only else k

        # Perform semantic search with filters
        print(f"Performing semantic search: {enhanced_query}")
        # Only pass filters if they're not empty
        if filters:
            results_with_scores = vectordb.similarity_search_with_score(enhanced_query, k=fetch_k, filter=filters)
            # Sort by score (lower is better for distance metrics)
            results_with_scores = sorted(results_with_scores, key=lambda x: -x[1])
        else:
            raw_results = vectordb.similarity_search(enhanced_query, k=fetch_k)
            # Create tuples with None score for consistency
            results_with_scores = [(doc, None) for doc in raw_results]

        # Display results
        print(f"\nFound {len(results_with_scores)} relevant course{'s' if len(results_with_scores) != 1 else ''}:")

        if(len(results_with_scores)==0):
            print("No results found with filters. Trying without filters.")
            raw_results = vectordb.similarity_search(enhanced_query, k=fetch_k)
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

        # Deduplicate by course_code if unique_courses_only is True
        if unique_courses_only:
            seen_codes = set()
            unique_dicts = []
            for course_dict in course_dicts:
                # Stop if we already have k unique courses
                if len(unique_dicts) >= k:
                    break

                course_code = course_dict.get('course_code')
                if course_code and course_code not in seen_codes:
                    seen_codes.add(course_code)
                    unique_dicts.append(course_dict)
                elif not course_code:  # Keep courses without a code
                    unique_dicts.append(course_dict)

            print(f"\nDeduplication: {len(course_dicts)} total results -> {len(unique_dicts)} unique courses (requested: {k})")
            return unique_dicts

        # If not unique_courses_only, return up to k results
        return course_dicts[:k]
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

if __name__ == "__main__":
    # Example queries
    queries = [
        "Find me a IEOR class about optimization after 10am on Tuesday and Thursday",
        "Find some CS classes that are interesting"
    ]

    for query in queries:
        filters, text_query, unique_only = generate_filters_from_prompt(query)
        print(f"Filters: {filters}")
        print(f"Text Query: {text_query}")
        print(f"Unique Courses Only: {unique_only}")
        results = query_courses_with_filters(text_query, filters=filters, k=10, conversation_context="", unique_courses_only=unique_only)
        print(results)
   