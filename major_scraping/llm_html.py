import json
import re
import os
import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

def clean_json_response(response_content: str) -> str:
    """Remove markdown code blocks from LLM response."""
    # Remove ```json and ``` markers
    cleaned = re.sub(r'^```json\s*', '', response_content)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    return cleaned.strip()

def parse_department_html(overview_html: str, requirements_html: str) -> dict:
    """
    Use an LLM (gpt-4o-mini) via LangChain to parse JSON file 
    into a structured JSON according to your spec.
    """
    # Remove temperature parameter since this model doesn't support it
    llm = ChatOpenAI(model_name="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = """
You are an expert parser.  

Extract and output JSON with these top‐level keys:
- department_code: string
- department_name: string
- website: string
- overview_sections: [
    { "section_name": string, "paragraphs": [string, ...] },
    ...
  ]
- department_wide_requirements: same shape as overview_sections but EXCLUDE any sections whose title contains "major", "minor", or "concentration"
- majors: {
    "<dept_code><n>": {
      "major_name": string,
      "description": [string, ...],
      "course_requirements": [
        { "rows": [[...], ...], "html": "..." },
        ...
      ],
      "footnotes": [string, ...]
    },
    ...
  }

Only output valid JSON—no extra commentary.
"""

    human_prompt = f"""
Overview HTML:
{overview_html}

Requirements HTML:
{requirements_html}

Please parse these and return the JSON.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        print(f"Response content: {repr(response.content)}")
        
        if not response.content or response.content.strip() == "":
            raise ValueError("LLM returned empty response")
        
        # Clean the response to remove markdown formatting
        cleaned_content = clean_json_response(response.content)
        print(f"Cleaned content: {repr(cleaned_content)}")
            
        # Try to parse the JSON
        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {response.content}")
            print(f"Cleaned response: {cleaned_content}")
            raise ValueError(f"LLM did not return valid JSON: {e}")
            
    except Exception as e:
        print(f"Error calling LLM: {e}")
        raise

def fetch_department_sections_html(url: str) -> tuple[str, str]:
    """Fetch overview and requirements HTML blocks directly from a department URL."""
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    overview_container = soup.find(id="textcontainer")
    requirements_container = soup.find(id="requirementstextcontainer")

    overview_html = overview_container.prettify() if overview_container else ""
    requirements_html = requirements_container.prettify() if requirements_container else ""
    return overview_html, requirements_html

def main():
    # Example department URL; can be parameterized
    url = os.environ.get("MAJOR_URL", "https://bulletin.columbia.edu/columbia-college/departments-instruction/mathematics/")
    overview_html, requirements_html = fetch_department_sections_html(url)

    parsed = parse_department_html(overview_html, requirements_html)

    output_path = os.environ.get("LLM_OUTPUT_PATH", "major_scraping/llm_comprehensive.json")
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(parsed, out, ensure_ascii=False, indent=2)
    print(f"➡️ Saved parsed JSON to {output_path}")

if __name__ == "__main__":
    main()
