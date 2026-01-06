import sys
from pathlib import Path

# Add project root to path for imports when running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from typing import List, Optional, Tuple

from backend.databases.data.misc.department_codes import dept_codes
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from agent.llm_manager import llm_manager
from agent.prompt_manager import prompt_manager


# A pydantic schema for the course query
class CourseQuery(BaseModel):

    department_codes: List[str] = Field(
        description=(
        "List of department codes ONLY if the user explicitly mentions specific departments. "
        "Use the exact department codes provided in the prompt (e.g., 'COMS', 'MATH', 'STAT'). "
        )
    )
    scheduled_days: List[str] = Field(description="Day abbreviations M,T,W,R,F. Do not put a comma between days.")
    scheduled_time_start: Optional[int] = Field(description="Earliest start time in minutes from midnight.Earliest is 0 by default.")
    scheduled_time_end: Optional[int] = Field(description="Latest end time in minutes from midnight. Latest is 1439 by default.")
    credits: Optional[float] = Field(description="Number of credits the course is worth. If the user does not specify a credit amount, do not include this field.")
    type_of_course: Optional[str] = Field(description="Type of course, such as 'LECTURE', 'SEMINAR', 'LAB', 'RECITATION', 'OTHER'. If the user does not specify a type, do not include this field.")


def generate_filters_from_prompt(user_prompt: str) -> Tuple[dict, str, bool]: # conversation_context: str = ""
    """
    Generates both filters and text query from the user's query in a single LLM call.
    Includes department codes directly in the prompt and only assigns them if explicitly requested.
    
    Args:
        user_prompt: A string containing the user's query
        conversation_context: Optional conversation history for context
    
    Returns:
        A tuple containing (filter_dict, text_query)
    """

    # Create langchain chain with prompt template and structured LLM.
    # Pre-fill dept_codes once so callers don't need to pass it each time.
    prompt_template = PromptTemplate.from_template(
        prompt_manager.get_prompt("filter_generation")
    ).partial(dept_codes=dept_codes)

    llm = llm_manager.get_llm(
        model_provider="openai",
        model="gpt-4o-2024-11-20",
        temperature=0.0,
        use_structured_output=True,
        structured_output_class=CourseQuery
    )

    chain = prompt_template | llm

    result = chain.invoke({
        "user_prompt": user_prompt,
        # "conversation_context": conversation_context,
    })

    filter_dict = build_chroma_filters(result)

    return filter_dict

def build_chroma_filters(q: CourseQuery) -> dict:
    """
    Build a Chroma-compatible flat filter dict.
    Only include keys that the user actually constrained.
    """
    filters = {}

    # Department - now using direct department codes from LLM
    if q.department_codes:
        # print("department_codes: " + str(q.department_codes))
        # Validate that all codes exist in our department codes
        valid_codes = [code for code in q.department_codes if code in dept_codes.values()]
        
        if valid_codes:
            if len(valid_codes) == 1:
                filters["department_code"] = valid_codes[0]
            else:
                filters["department_code"] = {"$in": valid_codes}

    # Days - exact string match (e.g., "TR", "MWF")
    # Join requested days into concatenated string for exact matching
    if q.scheduled_days:
        # Sort to match database format: MTWRF order
        days_str = ''.join(sorted(q.scheduled_days, key=lambda d: 'MTWRF'.index(d) if d in 'MTWRF' else 99))
        filters["scheduled_days"] = days_str

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
    
    if q.type_of_course:
        filters["type_of_course"] = q.type_of_course
    
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

# Test the function
if __name__ == "__main__":
    user_prompt = "Find me a math or computer science class after 2pm"
    filters = generate_filters_from_prompt(user_prompt)
    print(f"Filters: {filters}")

    