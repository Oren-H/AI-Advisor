import os
from typing import Dict, List, Any, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
import json

# Import our existing modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_filters import generate_filters_from_prompt
from query_courses import query_courses_with_pre_generated_filters
from database_utils import load_vector_database

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Define the state schema
class CourseAdvisorState(TypedDict):
    user_query: str
    filters: Dict[str, Any]
    course_results: List[Dict[str, Any]]
    course_info_json: str
    response: str
    error: str

def generate_filters_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate metadata filters from user query using the existing generate_filters module."""
    try:
        print(f"🔍 Generating filters for query: {state['user_query']}")
        filters = generate_filters_from_prompt(state['user_query'])
        print(f"✅ Generated filters: {filters}")
        return {**state, "filters": filters, "error": ""}
    except Exception as e:
        print(f"❌ Error generating filters: {e}")
        return {**state, "filters": {}, "error": f"Failed to generate filters: {str(e)}"}

def search_courses_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Search for courses using the generated filters and vector search."""
    try:
        print(f"🔎 Searching courses with filters: {state['filters']}")
        
        # Use the pre-generated filters from the previous node
        course_results = query_courses_with_pre_generated_filters(
            state['user_query'], 
            state['filters'], 
            k=5
        )
        
        # Convert to JSON string for the conversational agent
        course_info_json = json.dumps(course_results, indent=2)
        
        print(f"✅ Found {len(course_results)} courses")
        return {**state, "course_results": course_results, "course_info_json": course_info_json, "error": ""}
        
    except Exception as e:
        print(f"❌ Error searching courses: {e}")
        return {**state, "course_results": [], "course_info_json": "[]", "error": f"Failed to search courses: {str(e)}"}

def generate_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate the final response using the conversational agent template."""
    try:
        if state.get("error"):
            return {**state, "response": f"I encountered an error: {state['error']}. Please try rephrasing your query."}
        
        if not state.get("course_results"):
            return {**state, "response": "I couldn't find any courses matching your criteria. Please try broadening your search or rephrasing your query."}
        
        # Use the existing prompt template from conversational_agent.py
        prompt_template = ChatPromptTemplate.from_template("""
You are **Classify**, an AI peer-advisor that helps Columbia students compare and choose classes.

## Your Mission
1. **Parse the course objects in COURSE_INFO**.
2. **Summarize** the key details (title, level of math/theory, schedule, professor, prerequisites, credits).
3. **Highlight differences** (e.g. depth of math, project vs. proof focus, workload, grading style).
4. Offer **tailored suggestions** or next steps based on the user's goals, schedule, background, and preferences.
5. If the user's request is vague or contradictory, **ask a brief clarifying question** before giving recommendations.
6. Use **concise, friendly prose**—imagine you're a knowledgeable junior helping a first-year friend.
7. When helpful, format information with:
   * bullet lists (•) for per-course summaries,
   * **bold** for crucial distinctions,
   * *italics* for caveats or tips,
   * inline links supplied in the data (do **not** invent URLs).

## Constraints
- **Do not** output the raw COURSE_INFO block.
- Rely only on the courses provided; if the user asks about something else, politely say you only have those courses right now.
- Keep responses under **≈250 words** unless the user explicitly asks for more detail.
- Never fabricate prerequisites, meeting times, or professor names.

COURSE_INFO:
{course_info}

USER QUERY: {user_query}

Please provide your response:
""")
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.7
        )
        
        # Create the chain
        chain = prompt_template | llm
        
        # Generate response
        response = chain.invoke({
            "course_info": state["course_info_json"],
            "user_query": state["user_query"]
        })
        
        print(f"✅ Generated response for user query")
        return {**state, "response": response.content, "error": ""}
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return {**state, "response": f"I encountered an error while generating a response: {str(e)}", "error": str(e)}

def should_continue(state: CourseAdvisorState) -> str:
    """Determine if we should continue processing or end."""
    if state.get("error"):
        return "end"
    return "continue"

# Create the graph
def create_course_advisor_graph():
    """Create the LangGraph for the course advisor."""
    
    # Create the workflow
    workflow = StateGraph(CourseAdvisorState)
    
    # Add nodes
    workflow.add_node("generate_filters", generate_filters_node)
    workflow.add_node("search_courses", search_courses_node)
    workflow.add_node("generate_response", generate_response_node)
    
    # Add edges
    workflow.add_edge(START, "generate_filters")
    workflow.add_edge("generate_filters", "search_courses")
    workflow.add_edge("search_courses", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Compile the graph
    return workflow.compile()

def run_course_advisor(user_query: str) -> str:
    """
    Run the complete course advisor workflow.
    
    Args:
        user_query: The user's natural language query about courses
    
    Returns:
        The AI advisor's response
    """
    # Create the graph
    graph = create_course_advisor_graph()
    
    # Initialize state
    initial_state = {
        "user_query": user_query,
        "filters": {},
        "course_results": [],
        "course_info_json": "",
        "response": "",
        "error": ""
    }
    
    # Run the graph
    print(f"\n🚀 Starting course advisor workflow for: '{user_query}'")
    result = graph.invoke(initial_state)
    
    return result["response"]

def interactive_course_advisor():
    """Run an interactive version of the course advisor."""
    print("🎓 AI Course Advisor - Columbia University")
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    while True:
        user_query = input("You: ").strip()
        
        if user_query.lower() in ["exit", "quit"]:
            print("👋 Goodbye! Good luck with your course selection!")
            break
        
        if not user_query:
            print("Please enter a query about courses.")
            continue
        
        try:
            response = run_course_advisor(user_query)
            print(f"\nAI: {response}\n")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.\n")

if __name__ == "__main__":
    # Check if vector database exists
    try:
        # Use the correct path to the database (at the root level)
        # Get the absolute path to ensure it works regardless of where the script is run from
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels: rag/agent/ -> rag/ -> root, then add chroma_db
        chroma_db_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "chroma_db")
        load_vector_database(chroma_db_path)
        interactive_course_advisor()
    except FileNotFoundError:
        print("❌ Vector database not found!")
        print("Please run build_vector_db.py first to create the database.")
    except Exception as e:
        print(f"❌ Error: {e}") 