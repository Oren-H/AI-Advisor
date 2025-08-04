import os
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from app.db_querying.department_codes import dept_codes
from app.prompt_manager import prompt_manager
from app.llm_manager import llm_manager

# A pydantic schema for the course query
class CourseQuery(BaseModel):
    text_query: str = Field(
        description="Free-text keywords that should be used for vector search.")
    department_codes: List[str] = Field(
        description=(
        "List of department codes ONLY if the user explicitly mentions specific departments. "
        "Use the exact department codes provided in the prompt (e.g., 'COMS', 'MATH', 'STAT'). "
        "Only include codes if the user specifically names departments like 'computer science', "
        "'mathematics', 'statistics', etc. Do NOT assign codes for general topics."
        )
    )
    scheduled_days: List[str] = Field(description="Day abbreviations M,T,W,Th,F.")
    scheduled_time_start: Optional[int] = Field(description="Earliest start time in minutes from midnight")
    scheduled_time_end: Optional[int] = Field(description="Latest end time in minutes from midnight")
    credits: Optional[float] = Field(description="Number of credits the course is worth.")
    type: Optional[str] = Field(description="Type of course, such as 'LECTURE', 'SEMINAR', 'LAB', 'RECITATION', 'OTHER'.")

def generate_filters_from_prompt(user_prompt: str, conversation_context: str = "") -> Tuple[dict, str]:
    """
    Generates both filters and text query from the user's query in a single LLM call.
    Includes department codes directly in the prompt and only assigns them if explicitly requested.
    
    Args:
        user_prompt: A string containing the user's query
        conversation_context: Optional conversation history for context
    
    Returns:
        A tuple containing (filter_dict, text_query)
    """
    # Create langchain chain with prompt template and structured LLM
    prompt_template = PromptTemplate.from_template(
        prompt_manager.get_prompt("filter_generation")
    )
    
    llm = llm_manager.get_llm(
        model_provider="openai",
        temperature=0,
        use_structured_output=True,
        structured_output_class=CourseQuery
    )
    chain = prompt_template | llm
    
    result = chain.invoke({
        "user_prompt": user_prompt,
        "conversation_context": conversation_context
    })
    
    filter_dict = build_chroma_filters(result)
    return filter_dict, result.text_query

def build_chroma_filters(q: CourseQuery) -> dict:
    """
    Build a Chroma-compatible flat filter dict.
    Only include keys that the user actually constrained.
    """
    filters = {}

    # Department - now using direct department codes from LLM
    if q.department_codes:
        print("department_codes: " + str(q.department_codes))
        # Validate that all codes exist in our department codes
        valid_codes = [code for code in q.department_codes if code in dept_codes.values()]
        
        if valid_codes:
            if len(valid_codes) == 1:
                filters["department_code"] = valid_codes[0]
            else:
                filters["department_code"] = {"$in": valid_codes}

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

# Test the function
if __name__ == "__main__":
    user_prompt = "Find me a stats or simulations class that is computational and not proof based"
    filters, text_query = generate_filters_from_prompt(user_prompt, conversation_context="")
    print(f"Text Query: {text_query}")
    print(f"Filters: {filters}")
    