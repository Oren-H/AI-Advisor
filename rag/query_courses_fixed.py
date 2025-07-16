from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from database_utils import load_vector_database
import re

def query_courses_simple(query, k=5):
    """
    Query the course database using simple similarity search.
    
    Args:
        query (str): Natural language query about courses
        k (int): Number of results to return
    
    Returns:
        List of relevant course documents
    """
    try:
        vectordb = load_vector_database()
        
        print(f"Querying: {query}")
        results = vectordb.similarity_search(query, k=k)
        
        print(f"\nFound {len(results)} relevant courses:")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc.metadata['course_title']} ({doc.metadata['course_code']})")
            print(f"   Department: {doc.metadata['dept']}")
            print(f"   Credits: {doc.metadata['credits']}")
            print(f"   Instructor: {doc.metadata['instructor']}")
            print(f"   Times: {doc.metadata['times']}")
            print(f"   Currently Offered: {doc.metadata['offered']}")
            print(f"   Content: {doc.page_content[:200]}...")
        
        return results
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

def query_courses_with_filters(query, k=5):
    """
    Query the course database with manual filter parsing.
    
    Args:
        query (str): Natural language query about courses
        k (int): Number of results to return
    
    Returns:
        List of relevant course documents
    """
    try:
        vectordb = load_vector_database()
        
        # Simple keyword-based filter extraction
        filters = {}
        
        # Check for department mentions
        dept_patterns = {
            'COMS': ['computer science', 'coms', 'cs'],
            'CSEE': ['csee'],
            'MATH': ['math', 'mathematics'],
            'PHYS': ['physics', 'phys'],
            'RELI': ['religion', 'religious', 'reli'],
            'ARAM': ['aramaic', 'aram']
        }
        
        query_lower = query.lower()
        for dept_code, keywords in dept_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                filters['dept'] = dept_code
                break
        
        # Check for credit mentions
        credit_match = re.search(r'(\d+(?:\.\d+)?)\s*credit', query_lower)
        if credit_match:
            filters['credits'] = float(credit_match.group(1))
        
        print(f"Querying: {query}")
        print(f"Extracted filters: {filters}")
        
        # Use similarity search first
        results = vectordb.similarity_search(query, k=k*2)
        
        # Apply filters manually
        filtered_results = []
        for doc in results:
            matches_filters = True
            for field, value in filters.items():
                if field in doc.metadata:
                    if field == 'credits':
                        if abs(doc.metadata[field] - value) > 0.1:  # Allow small float differences
                            matches_filters = False
                            break
                    elif doc.metadata[field] != value:
                        matches_filters = False
                        break
                else:
                    matches_filters = False
                    break
            
            if matches_filters:
                filtered_results.append(doc)
                if len(filtered_results) >= k:
                    break
        
        print(f"\nFound {len(filtered_results)} relevant courses:")
        for i, doc in enumerate(filtered_results, 1):
            print(f"\n{i}. {doc.metadata['course_title']} ({doc.metadata['course_code']})")
            print(f"   Department: {doc.metadata['dept']}")
            print(f"   Credits: {doc.metadata['credits']}")
            print(f"   Instructor: {doc.metadata['instructor']}")
            print(f"   Times: {doc.metadata['times']}")
            print(f"   Currently Offered: {doc.metadata['offered']}")
            print(f"   Content: {doc.page_content[:200]}...")
        
        return filtered_results
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

if __name__ == "__main__":
    # Example queries
    queries = [
        "Show me computer science courses",
        "Show me COMS courses with 3 credits",
        "Show me physics courses",
        "Show me math courses with 4 credits",
    ]
    
    for query in queries:
        print("=" * 60)
        print("Using simple similarity search:")
        query_courses_simple(query)
        print("\nUsing filter-based search:")
        query_courses_with_filters(query)
        print() 