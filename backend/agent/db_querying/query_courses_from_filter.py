import os
import sys
from pathlib import Path

# Add project root to path for imports when running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from databases.database_utils import load_vector_database
from databases.paths import str_course_db_dir
from agent.db_querying.generate_course_filters import generate_filters_from_prompt
from agent.database_cache import db_cache

def query_courses_with_filters(
    query: str, filters: dict = None, 
    k: int = 10, 
    conversation_context: str = "",
    unique_courses_only: bool = True, 
    reruns: int = 3
):
    """
    Query the course database with filters and semantic search.

    Args:
        query (str): Natural language query about courses
        filters (dict): Metadata filters to apply (from generate_filters)
        k (int): Number of results to return
        conversation_context (str): Optional conversation history for context
        unique_courses_only (bool): If True, return only one section per unique course.
                                     If False, return all matching sections (useful for schedule planning).
        reruns (int): Number of widening attempts to ensure at least k results.

    Returns:
        List of relevant course documents
    """
    try:
        # Use cached database instead of loading from disk every time
        try:
            vectordb = db_cache.get_course_db()
        except RuntimeError:
            # Fallback for when running outside of FastAPI context (e.g., testing)
            vectordb = load_vector_database(str_course_db_dir())

        enhanced_query = query
        # if conversation_context:
        #     enhanced_query = f"Context: {conversation_context}\nQuery: {query}"

        # We'll widen the fetch size and aggregate unique courses across attempts
        base_multiplier = 3 if unique_courses_only else 1

        print(f"Performing semantic search: {enhanced_query}")

        # Accumulate unique documents by course_code first, before serialization
        selected_docs_with_scores = []
        seen_codes = set()

        # Helper to process and collect unique docs
        def collect_unique(results):
            for doc, score in results:
                if unique_courses_only:
                    course_code = doc.metadata.get('course_code')
                    if course_code:
                        if course_code in seen_codes:
                            continue
                        seen_codes.add(course_code)
                selected_docs_with_scores.append((doc, score))
                if len(selected_docs_with_scores) >= k:
                    break

        # Widening attempts (with filters if provided)
        for attempt in range(max(1, reruns)):
            fetch_k = k * base_multiplier * (attempt + 1)
            if filters:
                results_with_scores = vectordb.similarity_search_with_score(enhanced_query, k=fetch_k, filter=filters)
                # Sort by distance ascending: lower distance = more similar
                results_with_scores = sorted(results_with_scores, key=lambda x: x[1])
            else:
                raw_results = vectordb.similarity_search(enhanced_query, k=fetch_k)
                results_with_scores = [(doc, None) for doc in raw_results]

            print(f"\nAttempt {attempt + 1}/{max(1, reruns)}: fetched {len(results_with_scores)} results.")

            collect_unique(results_with_scores)
            if len(selected_docs_with_scores) >= k or not unique_courses_only:
                break

        # If still short on unique results and filters were used, broaden to unfiltered large pull
        if unique_courses_only and len(selected_docs_with_scores) < k and filters:
            extra_fetch_k = max(k * 5, k * base_multiplier * (reruns + 1))
            raw_results = vectordb.similarity_search(enhanced_query, k=extra_fetch_k)
            print(f"\nUnfiltered fallback fetch: {len(raw_results)} results.")
            collect_unique([(doc, None) for doc in raw_results])

        # # As a last resort, if still fewer than k and unique_courses_only is True, allow duplicates to reach k
        # if unique_courses_only and len(selected_docs_with_scores) < k:
        #     needed = k - len(selected_docs_with_scores)
        #     # Pull additional unfiltered docs and append regardless of course_code
        #     filler_fetch = max(k * 5, needed * 2)
        #     raw_results = vectordb.similarity_search(enhanced_query, k=filler_fetch)
        #     for doc in raw_results:
        #         selected_docs_with_scores.append((doc, None))
        #         if len(selected_docs_with_scores) >= k:
        #             break

        final_selection = selected_docs_with_scores[:min(k, len(selected_docs_with_scores))]
        print(f"\nReturning {len(final_selection)} courses (requested: {k}).")

        # Convert Document objects to dictionaries for JSON serialization
        course_dicts = []
        for i, (doc, score) in enumerate(final_selection, 1):
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

            score_text = f" (distance: {score:.4f})" if score is not None else ""
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
        "Optimization classes"
    ]

    for query in queries:
        filters = generate_filters_from_prompt(query)
        print(f"Filters: {filters}")
        results = query_courses_with_filters(query, filters=filters, k=10, reruns=3)
        print(f"Results: {results}")
   