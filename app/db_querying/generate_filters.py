import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from app.db_querying.department_codes import dept_codes

# Load environment variables from .env file
load_dotenv()

# A pydantic schema for the course query
class CourseQuery(BaseModel):
    text_query: str = Field(
        description="Free-text keywords that should be used for vector search.")
    department_descriptions: List[str] = Field(
        description=(
        "List of ALL department or field names the query refers to "
        "(e.g. 'math', 'statistics', 'computer science', 'physics'). "
        "Include broad synonyms such as 'mathy' or 'life-sciences'. "
        "Return plain names, not codes, and include every one that applies."
        "Example: 'literature' -> ['English', 'Literature']"
        "Example: 'simulation' -> ['Computer Science', 'Operations Research', 'Statistics', 'Math']"
        )
    )
    scheduled_days: List[str] = Field(description="Day abbreviations M,T,W,Th,F.")
    scheduled_time_start: Optional[int] = Field(description="Earliest start time in minutes from midnight")
    scheduled_time_end: Optional[int] = Field(description="Latest end time in minutes from midnight")
    credits: Optional[float] = Field(description="Number of credits the course is worth.")
    type: Optional[str] = Field(description="Type of course, such as 'LECTURE', 'SEMINAR', 'LAB', 'RECITATION', 'OTHER'.")

def generate_filters_from_prompt(user_prompt: str) -> dict:
    """
    Generates a dict containing filters with the proper logic based on the user's query.
    
    Args:
        user_prompt: A string containing the user's query
    
    Returns:
        A dict containing the filters with the proper logic based on the user's query
    """
    # Create a more specific prompt for better extraction
    enhanced_prompt = f"""
    Please analyze this course query and extract structured information:
    
    Query: "{user_prompt}"
    
    Instructions:
    1. For departments: Extract department names like "literature" (map to ENGL), "computer science" (map to COMS), "math" (map to MATH), etc.
    2. For time preferences (in minutes from midnight):
       - "mornings" = time_starting: 480 (8:00am), time_ending: 720 (12:00pm)
       - "afternoons" = time_starting: 720 (12:00pm), time_ending: 1020 (5:00pm)
       - "evenings" = time_starting: 1020 (5:00pm), time_ending: 1320 (10:00pm)
       - "early morning" = time_starting: 420 (7:00am), time_ending: 600 (10:00am)
       - "before 9:00 PM" = time_ending: 1260 (9:00pm)
       - "after 2:00 PM" = time_starting: 840 (2:00pm)
    3. For days: Extract day abbreviations (M, T, W, Th, F)
    4. For credits: Extract specific credit amounts
    5. For text_query: Extract keywords for semantic search, excluding department/time/day info
    """
    
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini").with_structured_output(CourseQuery, method="function_calling")
    result = llm.invoke(enhanced_prompt)
    filter_dict = build_chroma_filters(result)
    return filter_dict

def map_department_to_code(department_name: str, dept_codes: dict) -> List[str]:
    """
    Use an LLM to map a department name to its corresponding department code.
    
    Args:
        department_name: The department name to map
        dept_codes: Dictionary mapping department names to codes
    
    Returns:
        A list of department codes that most likely corresponds to the department name
    """
    # Create a prompt that lists all available departments and asks for the best match
    dept_list = "\n".join([f"- {dept}: {code}" for dept, code in dept_codes.items()])
    
    prompt = f"""
    Given the department name "{department_name}", please find the most likely match from the following list of Columbia University departments and their codes:

    {dept_list}

    Return ONLY the department code (e.g., "COMS", "MATH", etc.) that best matches the department name "{department_name}".
    If there's no good match, return "UNKNOWN".
    """
    
    # Use a different LLM instance for this mapping task
    mapping_llm = ChatOpenAI(temperature=0, model="gpt-4")
    response = mapping_llm.invoke(prompt)
    
    # Extract the department code from the response
    dept_code = response.content.strip()
    
    # Validate that the returned code exists in our dictionary
    if dept_code in dept_codes.values():
        return dept_code
    else:
        return "UNKNOWN"

def build_chroma_filters(q: CourseQuery) -> dict:
    """
    Build a Chroma-compatible flat filter dict.
    Only include keys that the user actually constrained.
    """
    filters = {}

    # Department
    if q.department_descriptions:
        # q.department is a list, so we need to map each department
        print("department_descriptions: " + str(q.department_descriptions))
        mapped_departments = []
        for department in q.department_descriptions:
            mapped = map_department_to_code(department, dept_codes)
            if mapped and mapped != "UNKNOWN":
                mapped_departments.append(mapped)
        
        if mapped_departments:
            if len(mapped_departments) == 1:
                filters["department_code"] = mapped_departments[0]
            else:
                filters["department_code"] = {"$in": mapped_departments}

    # Days (expecting q.days as iterable like ['T','Th'])
    if q.scheduled_days:
        filters["scheduled_days"] = {"$in": list(q.scheduled_days)}

    # Credits
    if q.credits is not None:
        # If multiple allowed (e.g. '3 or 4') you'd use {"$in": [3,4]}
        filters["credits"] = q.credits

    # Start time (prefer numeric minutes field)
    if q.scheduled_time_start:
        # If q.start_time is a datetime/time string, convert to minutes
        filters["scheduled_time_start"] = {"$gte": q.scheduled_time_start}

    # End time
    if q.scheduled_time_end:
        filters["scheduled_time_end"] = {"$lte": q.scheduled_time_end}
    
    if q.type:
        filters["type"] = q.type
    
    filters = to_chroma_where(filters)
    return filters

def to_chroma_where(flat: dict) -> dict:
    """
    Convert legacy flat filter {field: spec} into Chroma 1.x logical form.
    Scalars become {"$eq": scalar}. Operator dicts pass through unchanged.
    """
    clauses = []
    for field, spec in flat.items():
        if isinstance(spec, dict) and any(k.startswith("$") for k in spec):
            # already operator form
            clauses.append({field: spec})
        else:
            clauses.append({field: {"$eq": spec}})
    if not clauses:
        return {}
    if len(clauses) == 1:
        return clauses[0]          # legal: single-field filter
    return {"$and": clauses}

def get_text_query_from_prompt(user_prompt: str) -> str:
    """
    Extract the text query component from a user prompt for semantic search.
    
    Args:
        user_prompt: The user's natural language query
    
    Returns:
        Text query for semantic search
    """
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini").with_structured_output(CourseQuery, method="function_calling")
    result = llm.invoke(user_prompt)
    return result.text_query

# Test the function
if __name__ == "__main__":
    user_prompt = "Find me a stats or simulations class that is computational and not proof based"
    filters = generate_filters_from_prompt(user_prompt)
    text_query = get_text_query_from_prompt(user_prompt)
    print(f"Text Query: {text_query}")
    print(f"Filters: {filters}")
    