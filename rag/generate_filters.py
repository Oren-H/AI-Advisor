from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from department_codes import dept_codes

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
    filter_dict = build_filter(result)
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

def convert_time_to_minutes(time_str: str) -> int:
    """
    Convert time string (e.g., "3:00 PM") to minutes from midnight.
    
    Args:
        time_str: Time string in format like "3:00 PM" or "15:00"
    
    Returns:
        Minutes from midnight
    """
    try:
        # Handle 12-hour format
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            from datetime import datetime
            time_obj = datetime.strptime(time_str, "%I:%M %p")
            return time_obj.hour * 60 + time_obj.minute
        # Handle 24-hour format
        else:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
    except:
        return 0

def convert_days_to_chroma_format(days: List[str]) -> str:
    """
    Convert day abbreviations to Chroma-compatible format.
    
    Args:
        days: List of day abbreviations like ["M", "T", "W", "Th", "F"]
    
    Returns:
        String format like "MWF" or "TR"
    """
    valid_days = {"M", "T", "W", "Th", "F"}
    
    result = ""
    for day in days:
        if day in valid_days:
            result += day
    
    return result

def build_filter(q: CourseQuery) -> dict:
    """
    Builds a dict containing filters with the proper logic based on the user's query.
    Returns filters compatible with Chroma's metadata filtering.

    Args:
        q: A CourseQuery object containing the user's query
    
    Returns:
        A dict containing the filters with the proper logic based on the user's query
    """
    f = {}
    
    # Handle department filter
    if q.department:
        # Map the first department to code (for now, handle single department)
        if len(q.department) > 0:
            mapped_code = map_department_to_code(q.department[0], dept_codes)
            if mapped_code != "UNKNOWN":
                f["dept"] = mapped_code
    
    # Handle days filter - convert to Chroma format
    if q.days:
        days_str = convert_days_to_chroma_format(q.days)
        if days_str:
            f["days_offered"] = days_str
    
    # Handle credits filter
    if q.credits:
        f["credits"] = q.credits
    
    # Handle time filters - these will need special handling in the query function
    # since Chroma doesn't support complex time comparisons directly
    time_filters = {}
    if q.start_time:
        time_filters["start_time"] = q.start_time
    if q.end_time:
        time_filters["end_time"] = q.end_time
    
    if time_filters:
        f["_time_filters"] = time_filters  # Special key for post-processing
    
    return f

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
    user_prompt = "Find me a machine learning course in the computer science department that is offered on a Tuesday after 3:00 PM"
    filters = generate_filters_from_prompt(user_prompt)
    text_query = get_text_query_from_prompt(user_prompt)
    print(f"Text Query: {text_query}")
    print(f"Filters: {filters}")