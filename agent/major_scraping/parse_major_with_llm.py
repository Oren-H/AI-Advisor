import json
import sys
import os
from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
import tiktoken

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.llm_manager import llm_manager

# Global token counter
total_input_tokens = 0
total_output_tokens = 0

# Cache LLM instances to avoid recreation
_llm_cache = {}

def get_cached_llm(model: str = "gpt-4o", temperature: float = 0.1):
    """Get cached LLM instance to avoid recreation."""
    cache_key = f"{model}_{temperature}"
    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = llm_manager.get_llm(
            model_provider="openai", model=model, temperature=temperature
        )
    return _llm_cache[cache_key]

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens for a given text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        # Fallback for models not in tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

def print_token_stats():
    """Print current token usage statistics."""
    print(f"\n=== TOKEN USAGE ===")
    print(f"Input tokens: {total_input_tokens:,}")
    print(f"Output tokens: {total_output_tokens:,}")
    print(f"Total tokens: {(total_input_tokens + total_output_tokens):,}")
    print(f"Estimated cost (GPT-4o): ${(total_input_tokens * 0.0025 + total_output_tokens * 0.01) / 1000:.4f}")
    print("===================")

def parse_major_requirements_with_llm(major_name: str, major_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to parse complex major requirements into clean structured format."""
    
    # Create prompt for requirements parsing
    parsing_prompt = ChatPromptTemplate.from_template("""
You are a precise academic requirements parser. Convert the complex major requirements into clean JSON.

MAJOR: {major_name}

RAW REQUIREMENTS DATA:
{major_requirements}

Convert this into the following clean JSON structure:

{{
  "core_sequences": [
    {{
      "description": "Select one of the following calculus sequences",
      "credits": 15,
      "options": [
        {{
          "name": "Standard Sequence",
          "courses": [
            {{"code": "MATH UN1101", "title": "CALCULUS I", "credits": 3}},
            {{"code": "MATH UN1102", "title": "CALCULUS II", "credits": 3}}
          ]
        }},
        {{
          "name": "Honors Sequence", 
          "courses": [...]
        }}
      ]
    }}
  ],
  "required_courses": [
    {{"code": "MATH GU4041", "title": "INTRO MODERN ALGEBRA I", "credits": 3, "description": "Required core course"}}
  ],
  "elective_categories": [
    {{
      "name": "Mathematics Electives",
      "credits_required": 12,
      "description": "12 points from 2000+ level math courses",
      "restrictions": "At least 2000 level",
      "courses": []
    }}
  ],
  "tracks": [
    {{
      "name": "Track A",
      "minimum_credits": 9,
      "courses": [
        {{"code": "MATH UN2500", "title": "ANALYSIS AND OPTIMIZATION", "credits": 3}}
      ]
    }}
  ],
  "seminars": [
    {{
      "name": "Undergraduate Seminars",
      "credits_required": 3,
      "options": [
        {{"code": "MATH UN3951", "title": "UNDERGRADUATE SEMINARS I", "credits": 3}}
      ]
    }}
  ]
}}

IMPORTANT:
- Extract ALL course codes and titles exactly as they appear
- Identify sequences vs individual requirements vs elective buckets
- Pay attention to credit requirements and restrictions
- Group related requirements logically
- Include track information if present
- Don't invent course codes - use only what's provided

Output ONLY the JSON, no explanation.
""")

    # Get cached LLM
    llm = get_cached_llm()
    
    # Create chain
    chain = parsing_prompt | llm
    
    # Count input tokens
    input_text = parsing_prompt.format(
        major_name=major_name,
        major_requirements=json.dumps(major_data, indent=2)
    )
    input_tokens = count_tokens(input_text)
    
    # Parse requirements
    response = chain.invoke({
        "major_name": major_name,
        "major_requirements": json.dumps(major_data, indent=2)
    })
    
    # Count output tokens and update totals
    output_tokens = count_tokens(response.content)
    global total_input_tokens, total_output_tokens
    total_input_tokens += input_tokens
    total_output_tokens += output_tokens
    
    print(f"📊 Tokens used - Input: {input_tokens:,}, Output: {output_tokens:,}")
    
    try:
        # Clean up LLM response - remove markdown code blocks
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```
        content = content.strip()
        
        # Parse cleaned JSON
        parsed_requirements = json.loads(content)
        return parsed_requirements
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}")
        print(f"LLM Response: {response.content}")
        return None

def parse_cognates_with_llm(cognates_data: list) -> list:
    """Use LLM to parse cognate course lists into clean format."""
    
    cognates_prompt = ChatPromptTemplate.from_template("""
You are parsing a list of approved cognate courses. Extract each individual course into a clean list.

RAW COGNATES DATA:
{cognates_data}

Convert into this JSON format:
[
  {{"code": "COMS W3134", "title": "Data Structures in Java", "department": "COMS"}},
  {{"code": "ECON UN3025", "title": "FINANCIAL ECONOMICS", "department": "ECON"}}
]

IMPORTANT:
- Extract EVERY individual course code and title
- Split long text blocks into individual courses
- Include department prefix
- Don't invent - use exactly what's provided
- Skip descriptive text that isn't a course

Output ONLY the JSON array, no explanation.
""")

    llm = get_cached_llm()
    chain = cognates_prompt | llm
    
    # Count input tokens
    input_text = cognates_prompt.format(cognates_data=json.dumps(cognates_data, indent=2))
    input_tokens = count_tokens(input_text)
    
    response = chain.invoke({
        "cognates_data": json.dumps(cognates_data, indent=2)
    })
    
    # Count output tokens and update totals
    output_tokens = count_tokens(response.content)
    global total_input_tokens, total_output_tokens
    total_input_tokens += input_tokens
    total_output_tokens += output_tokens
    
    print(f"📊 Cognates tokens - Input: {input_tokens:,}, Output: {output_tokens:,}")
    
    try:
        # Clean up LLM response - remove markdown code blocks
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```
        content = content.strip()
        
        parsed_cognates = json.loads(content)
        return parsed_cognates
    except json.JSONDecodeError as e:
        print(f"Error parsing cognates JSON: {e}")
        return []

def parse_single_major(dept_code: str, major_name: str, major_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single major's requirements using LLM."""
    print(f"🤖 Parsing {dept_code}: {major_name} with LLM...")
    
    # Parse main requirements
    parsed_reqs = parse_major_requirements_with_llm(major_name, major_data)
    if not parsed_reqs:
        return None
    
    # Parse cognates if they exist
    cognates = []
    if "cognates" in major_data and major_data["cognates"]:
        cognates = parse_cognates_with_llm(major_data["cognates"])
    
    # Parse footnotes for additional context
    footnotes = major_data.get("footnotes", [])
    
    result = {
        "major_id": major_data.get("major_id", ""),
        "parsed_requirements": parsed_reqs,
        "cognates": cognates,
        "footnotes": footnotes,
        "raw_data": major_data  # Keep original for reference
    }
    
    print(f"✅ Parsed {len(parsed_reqs.get('required_courses', []))} required courses, {len(cognates)} cognates")
    return result

def parse_department_majors(dept_code: str, input_file: str = "major_scraping/data/major_data.json", 
                          output_file: str = "major_scraping/data/parsed_requirements.json"):
    """Parse all majors for a specific department using LLM."""
    
    # Load major data
    with open(input_file, 'r') as f:
        all_data = json.load(f)
    
    if dept_code not in all_data:
        print(f"❌ Department {dept_code} not found in data")
        return None
    
    dept_data = all_data[dept_code]
    if "majors" not in dept_data:
        print(f"❌ No majors found for {dept_code}")
        return None
    
    parsed_dept = {
        "department_code": dept_code,
        "department_name": dept_data.get("department_name", ""),
        "majors": {}
    }
    
    # Parse each major
    for major_name, major_data in dept_data["majors"].items():
        try:
            parsed_major = parse_single_major(dept_code, major_name, major_data)
            if parsed_major:
                parsed_dept["majors"][major_name] = parsed_major
        except Exception as e:
            print(f"❌ Error parsing {major_name}: {e}")
            continue
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(parsed_dept, f, indent=2)
    
    print(f"✅ Saved parsed requirements to {output_file}")
    print_token_stats()
    return parsed_dept

if __name__ == "__main__":
    # Test with Mathematics department
    result = parse_department_majors("MATH")
    
    if result:
        print(f"\n=== PARSING SUMMARY ===")
        print(f"Department: {result['department_name']}")
        print(f"Majors processed: {len(result['majors'])}")
        
        # Show sample from first major
        if result["majors"]:
            first_major = list(result["majors"].values())[0]
            reqs = first_major["parsed_requirements"]
            
            print(f"\nSample from first major:")
            print(f"{reqs}")
            print(f"- Core sequences: {len(reqs.get('core_sequences', []))}")
            print(f"- Required courses: {len(reqs.get('required_courses', []))}")
            print(f"- Elective categories: {len(reqs.get('elective_categories', []))}")
            print(f"- Cognates: {len(first_major.get('cognates', []))}")
        
        # Final token summary
        print_token_stats()