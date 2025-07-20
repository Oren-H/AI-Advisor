import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from department_codes import dept_codes

# Load environment variables from .env file
load_dotenv()

# A pydantic schema for the course query
class CourseQuery(BaseModel):
    text_query: str = Field(
        description="Free-text keywords that should be used for vector search.")
    department: List[str] = Field(
        description="Department that the course is offered in.")
    days: List[str] = Field(description="Day abbreviations M,T,W,Th,F.")
    start_time: Optional[int] = Field(description="Earliest start time in minutes from midnight.")
    end_time: Optional[int] = Field(description="Latest end time in minutes from midnight.")
    credits: Optional[float] = Field(description="Number of credits the course is worth.")

def generate_filters_from_prompt(user_prompt: str) -> dict:
    """
    Generates a dict containing filters with the proper logic based on the user's query.
    
    Args:
        user_prompt: A string containing the user's query
    
    Returns:
        A dict containing the filters with the proper logic based on the user's query
    """
    llm = ChatOpenAI(temperature=0, model="gpt-4").with_structured_output(CourseQuery, method="function_calling")
    result = llm.invoke(user_prompt)
    filter_dict = build_chroma_filters(result)
    return filter_dict

def map_department_to_code(department_name: str, dept_codes: dict) -> str:
    """
    Use an LLM to map a department name to its corresponding department code.
    
    Args:
        department_name: The department name to map
        dept_codes: Dictionary mapping department names to codes
    
    Returns:
        The department code that most likely corresponds to the department name
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
    if q.department:
        mapped = map_department_to_code(q.department, dept_codes)
        if mapped:    
            filters["dept"] = mapped

    # Days (expecting q.days as iterable like ['T','Th'])
    if q.days:
        filters["days_offered"] = {"$in": list(q.days)}

    # Credits
    if q.credits is not None:
        # If multiple allowed (e.g. '3 or 4') you'd use {"$in": [3,4]}
        filters["credits"] = q.credits

    # Start time (prefer numeric minutes field)
    if q.start_time:
        # If q.start_time is a datetime/time string, convert to minutes
        filters["time_starting"] = {"$gte": q.start_time}

    # End time
    if q.end_time:
        filters["time_ending"] = {"$lte": q.end_time}
    
    filters["offered"] = True
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
    llm = ChatOpenAI(temperature=0, model="gpt-4").with_structured_output(CourseQuery, method="function_calling")
    result = llm.invoke(user_prompt)
    return result.text_query

# Test the function
if __name__ == "__main__":
    user_prompt = "Find me an ml course in the computer science department that is offered on a Tuesday after 3:00 PM"
    filters = generate_filters_from_prompt(user_prompt)
    text_query = get_text_query_from_prompt(user_prompt)
    print(f"Text Query: {text_query}")
    print(f"Filters: {filters}")