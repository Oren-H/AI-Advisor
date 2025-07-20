import json
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from database_utils import load_vector_database
from generate_filters import generate_filters_from_prompt, get_text_query_from_prompt

def convert_time_to_minutes(time_str: str) -> int:
    """
    Convert time string from database format to minutes from midnight.
    
    Args:
        time_str: Time string like "3:00PM" or "15:00"
    
    Returns:
        Minutes from midnight
    """
    try:
        # Handle formats like "3:00PM"
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            from datetime import datetime
            # Try different formats
            for fmt in ["%I:%M%p", "%I:%M %p", "%H:%M"]:
                try:
                    time_obj = datetime.strptime(time_str, fmt)
                    return time_obj.hour * 60 + time_obj.minute
                except:
                    continue
        # Handle 24-hour format
        else:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
    except:
        return 0

def apply_metadata_filters(docs: List, filters: Dict) -> List:
    """
    Apply metadata filters to documents after retrieval.
    
    Args:
        docs: List of document objects
        filters: Dict with metadata filters
    
    Returns:
        Filtered list of documents
    """
    filtered_docs = []
    
    for doc in docs:
        metadata = doc.metadata
        passes_filters = True
        
        # Check department filter
        if "dept" in filters:
            if metadata.get("dept", "") != filters["dept"]:
                passes_filters = False
        
        # Check days filter
        if "days_offered" in filters:
            if filters["days_offered"] not in metadata.get("days_offered", ""):
                passes_filters = False
        
        # Check credits filter
        if "credits" in filters:
            if metadata.get("credits", 0) != filters["credits"]:
                passes_filters = False
        
        # Check time filters
        if "_time_filters" in filters:
            time_filters = filters["_time_filters"]
            start_time_str = metadata.get("time_starting", "")
            end_time_str = metadata.get("time_ending", "")
            
            if start_time_str and end_time_str:
                doc_start_minutes = convert_time_to_minutes(start_time_str)
                doc_end_minutes = convert_time_to_minutes(end_time_str)
                
                if "start_time" in time_filters:
                    # User wants courses that start after this time
                    if doc_start_minutes < time_filters["start_time"]:
                        passes_filters = False
                        
                if "end_time" in time_filters:
                    # User wants courses that end before this time
                    if doc_end_minutes > time_filters["end_time"]:
                        passes_filters = False
        
        if passes_filters:
            filtered_docs.append(doc)
    
    return filtered_docs

def document_to_json(doc) -> Dict[str, Any]:
    """
    Convert a document object to JSON format compatible with conversational agent.
    
    Args:
        doc: Document object from vector database
    
    Returns:
        Dictionary with course information
    """
    metadata = doc.metadata
    
    # Extract description and prerequisites from page content
    content = doc.page_content
    description = ""
    prerequisites = ""
    
    # Parse the content to extract description and prerequisites
    lines = content.split('\n')
    for line in lines:
        if line.startswith('Description:'):
            description = line.replace('Description:', '').strip()
        elif line.startswith('Prerequisites:'):
            prerequisites = line.replace('Prerequisites:', '').strip()
    
    return {
        "course_code": metadata.get("course_code", ""),
        "title": metadata.get("course_title", ""),
        "dept": metadata.get("dept", ""),
        "credits": metadata.get("credits", 0.0),
        "times": f"{metadata.get('time_starting', '')} - {metadata.get('time_ending', '')}",
        "instructor": metadata.get("instructor", ""),
        "prerequisites": prerequisites,
        "description": description,
        "link": metadata.get("url", ""),
        "days_offered": metadata.get("days_offered", ""),
        "enrolled": metadata.get("enrolled", ""),
        "max_enrollment": metadata.get("max_enrollment", ""),
        "offered": metadata.get("offered", False)
    }

def get_department_courses(vectordb, dept: str) -> List:
    """
    Get all courses from a specific department.
    
    Args:
        vectordb: Vector database
        dept: Department code
    
    Returns:
        List of document objects
    """
    # Get all documents directly from the collection
    collection = vectordb._collection
    all_docs = collection.get()
    
    dept_courses = []
    for i, metadata in enumerate(all_docs['metadatas']):
        if metadata and metadata.get('dept') == dept:
            # Create a document object
            from langchain_core.documents import Document
            doc = Document(
                page_content=all_docs['documents'][i],
                metadata=metadata
            )
            dept_courses.append(doc)
    
    return dept_courses

def query_courses_with_filters(user_prompt: str, k: int = 5) -> str:
    """
    Query courses using natural language prompt, convert to filters, and return JSON.
    
    Args:
        user_prompt: Natural language query about courses
        k: Number of results to return
    
    Returns:
        JSON string with course information for conversational agent
    """
    try:
        # Load vector database
        vectordb = load_vector_database()
        
        # Generate filters from prompt
        filters = generate_filters_from_prompt(user_prompt)
        text_query = get_text_query_from_prompt(user_prompt)
        
        print(f"Text Query: {text_query}")
        print(f"Generated Filters: {filters}")
        
        # Strategy: If we have a department filter, get all courses from that department first
        if "dept" in filters:
            dept = filters["dept"]
            print(f"Getting all courses from department: {dept}")
            
            # Get all courses from the department
            dept_courses = get_department_courses(vectordb, dept)
            print(f"Found {len(dept_courses)} courses in {dept}")
            
            # Apply semantic search within department courses
            if text_query and text_query.strip():
                # Create a simple similarity search within department courses
                # We'll use the text content for similarity
                scored_courses = []
                for doc in dept_courses:
                    # Simple keyword matching for now
                    content_lower = doc.page_content.lower()
                    query_lower = text_query.lower()
                    
                    # Count matching words
                    query_words = query_lower.split()
                    matches = sum(1 for word in query_words if word in content_lower)
                    score = matches / len(query_words) if query_words else 0
                    
                    scored_courses.append((doc, score))
                
                # Sort by score and take top results
                scored_courses.sort(key=lambda x: x[1], reverse=True)
                docs = [doc for doc, score in scored_courses if score > 0]
            else:
                docs = dept_courses
        else:
            # No department filter, use general semantic search
            results = vectordb.similarity_search_with_relevance_scores(
                query=text_query,
                k=k * 3
            )
            docs = [doc for doc, score in results]
        
        # Apply remaining metadata filters
        if filters:
            docs = apply_metadata_filters(docs, filters)
        
        # Limit to k results
        docs = docs[:k]
        
        # Convert to JSON format
        courses_json = [document_to_json(doc) for doc in docs]
        
        # Return as JSON string
        return json.dumps(courses_json, indent=2)
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return json.dumps([])

def query_courses_simple(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Simple query function that returns course data as a list of dictionaries.
    
    Args:
        query: Natural language query about courses
        k: Number of results to return
    
    Returns:
        List of course dictionaries
    """
    json_str = query_courses_with_filters(query, k)
    return json.loads(json_str)

def print_course_results(courses: List[Dict[str, Any]]):
    """
    Print course results in a readable format.
    
    Args:
        courses: List of course dictionaries
    """
    print(f"\nFound {len(courses)} relevant course{'s' if len(courses) != 1 else ''}:")
    
    for i, course in enumerate(courses, 1):
        print(f"\n{i}. {course['title']} ({course['course_code']})")
        print(f"   Department: {course['dept']}")
        print(f"   Credits: {course['credits']}")
        print(f"   Instructor: {course['instructor']}")
        print(f"   Times: {course['times']}")
        print(f"   Days: {course['days_offered']}")
        print(f"   Enrolled: {course['enrolled']} / {course['max_enrollment']}")
        print(f"   Currently Offered: {course['offered']}")
        if course['description']:
            print(f"   Description: {course['description'][:100]}...")
        if course['prerequisites']:
            print(f"   Prerequisites: {course['prerequisites']}")

def query_courses_with_pre_generated_filters(user_prompt: str, pre_generated_filters: dict, k: int = 5) -> List[Dict[str, Any]]:
    """
    Query courses using pre-generated filters to avoid duplicate filter generation.
    
    Args:
        user_prompt: Natural language query about courses
        pre_generated_filters: Filters already generated from generate_filters_from_prompt
        k: Number of results to return
    
    Returns:
        List of course dictionaries
    """
    try:
        # Load vector database with correct path
        vectordb = load_vector_database("../chroma_db")
        
        # Use pre-generated filters instead of generating new ones
        filters = pre_generated_filters
        text_query = get_text_query_from_prompt(user_prompt)
        
        print(f"Text Query: {text_query}")
        print(f"Using Pre-generated Filters: {filters}")
        
        # Strategy: If we have a department filter, get all courses from that department first
        if "dept" in filters:
            dept = filters["dept"]
            print(f"Getting all courses from department: {dept}")
            
            # Get all courses from the department
            dept_courses = get_department_courses(vectordb, dept)
            print(f"Found {len(dept_courses)} courses in {dept}")
            
            # Apply semantic search within department courses
            if text_query and text_query.strip():
                # Create a simple similarity search within department courses
                # We'll use the text content for similarity
                scored_courses = []
                for doc in dept_courses:
                    # Simple keyword matching for now
                    content_lower = doc.page_content.lower()
                    query_lower = text_query.lower()
                    
                    # Count matching words
                    query_words = query_lower.split()
                    matches = sum(1 for word in query_words if word in content_lower)
                    score = matches / len(query_words) if query_words else 0
                    
                    scored_courses.append((doc, score))
                
                # Sort by score and take top results
                scored_courses.sort(key=lambda x: x[1], reverse=True)
                docs = [doc for doc, score in scored_courses if score > 0]
            else:
                docs = dept_courses
        else:
            # No department filter, use general semantic search
            results = vectordb.similarity_search_with_relevance_scores(
                query=text_query,
                k=k * 3
            )
            docs = [doc for doc, score in results]
        
        # Apply remaining metadata filters
        if filters:
            docs = apply_metadata_filters(docs, filters)
        
        # Limit to k results
        docs = docs[:k]
        
        # Convert to JSON format
        courses_json = [document_to_json(doc) for doc in docs]
        
        return courses_json
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

if __name__ == "__main__":
    # Example queries
    test_queries = [
        "Find me a machine learning course in the computer science department that is offered on a Tuesday after 3:00 PM",
        "Show me computer science courses with 3 credits",
        "Find calculus courses in the math department",
    ]
    
    for query in test_queries:
        print("=" * 80)
        print(f"Query: {query}")
        print("=" * 80)
        
        courses = query_courses_simple(query, k=3)
        print_course_results(courses)
        
        # Also show JSON format
        print(f"\nJSON format for conversational agent:")
        print(json.dumps(courses, indent=2))
        print() 