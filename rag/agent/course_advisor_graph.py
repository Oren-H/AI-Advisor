import os
from typing import Dict, List, Any, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import json

# Import our existing modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_filters import generate_filters_from_prompt
from query_courses_from_filter import query_courses_with_filters
from database_utils import load_vector_database

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Define the state schema
class CourseAdvisorState(TypedDict):
    user_query: str
    intent: str  # "specific", "advisory", or "mixed"
    filters: Dict[str, Any]
    course_results: List[Dict[str, Any]]
    course_info_json: str
    response: str
    error: str
    conversation_history: List[BaseMessage]  # Memory for conversation context
    user_profile: Dict[str, Any]  # Store user preferences and context

def intent_classification_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Classify the user's intent based on their query and conversation history."""
    try:
        print(f"🧠 Classifying intent for query: {state['user_query']}")
        
        # Get conversation history for context
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 4 exchanges for context)
        recent_history = history[-8:] if len(history) > 8 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Create a prompt for intent classification with memory
        intent_prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that classifies user queries about Columbia University courses and academic advice.

Consider the conversation history and user profile when classifying intent:

**USER PROFILE**: {user_profile}

**CONVERSATION HISTORY**:
{conversation_context}

Classify the user's intent into one of three categories:

**SPECIFIC**: User is asking for specific course recommendations, course comparisons, or detailed information about particular courses. Examples:
- "What are the best CS courses for beginners?"
- "Compare COMS 3157 and COMS 3134"
- "Show me advanced math courses"
- "What courses should I take for a data science minor?"

**ADVISORY**: User is asking for general academic advice, career guidance, or broader educational planning. Examples:
- "How should I plan my major?"
- "What's the best way to prepare for graduate school?"
- "Should I double major in CS and math?"
- "How do I balance coursework with research?"

**MIXED**: User wants a combination of advisory guidance with some course suggestions sprinkled in. Examples:
- "I want to study AI, what should I focus on and which courses would help?"
- "How can I prepare for a career in finance? Any specific courses?"
- "I'm interested in entrepreneurship, what's your advice and what classes should I take?"

Respond with ONLY one word: SPECIFIC, ADVISORY, or MIXED.

CURRENT USER QUERY: {user_query}

INTENT:
""")
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.1
        )
        
        # Create the chain
        chain = intent_prompt | llm
        
        # Classify intent
        intent_response = chain.invoke({
            "user_query": state['user_query'],
            "conversation_context": conversation_context,
            "user_profile": json.dumps(user_profile, indent=2)
        })
        intent = intent_response.content.strip().upper()
        
        # Validate the response
        if intent not in ["SPECIFIC", "ADVISORY", "MIXED"]:
            # Default to mixed if classification is unclear
            intent = "MIXED"
        
        print(f"✅ Classified intent as: {intent}")
        return {**state, "intent": intent.lower(), "error": ""}
        
    except Exception as e:
        print(f"❌ Error classifying intent: {e}")
        return {**state, "intent": "mixed", "error": f"Failed to classify intent: {str(e)}"}

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
        
        # Use the filters from the previous node
        course_results = query_courses_with_filters(
            state['user_query'], 
            filters=state['filters'], 
            k=5
        )
        
        # Convert to JSON string for the conversational agent
        course_info_json = json.dumps(course_results, indent=2)
        
        print(f"✅ Found {len(course_results)} courses")
        return {**state, "course_results": course_results, "course_info_json": course_info_json, "error": ""}
        
    except Exception as e:
        print(f"❌ Error searching courses: {e}")
        return {**state, "course_results": [], "course_info_json": "[]", "error": f"Failed to search courses: {str(e)}"}

def update_memory_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Update conversation memory and extract user profile information."""
    try:
        print(f"🧠 Updating memory for query: {state['user_query']}")
        
        # Get current conversation history
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Add the current user query to history
        history.append(HumanMessage(content=state["user_query"]))
        
        # Extract user profile information from the query
        profile_prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that extracts user profile information from conversations about Columbia University courses and academic planning.

From the user's query, extract any relevant information about:
- Academic level (first-year, sophomore, junior, senior, graduate)
- Major/minor interests or current major
- Academic goals (career, graduate school, research, etc.)
- Previous coursework or experience mentioned
- Preferences (course difficulty, workload, specific subjects)
- Constraints (schedule, prerequisites, etc.)

Return a JSON object with any extracted information. If no relevant information is found, return an empty object {}.

Previous conversation context:
{conversation_context}

Current user query: {user_query}

Extracted profile information (JSON only):
""")
        
        # Initialize the LLM for profile extraction
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.1
        )
        
        # Create the chain
        chain = profile_prompt | llm
        
        # Prepare conversation context (last 3 exchanges for context)
        recent_history = history[-6:] if len(history) > 6 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Extract profile information
        profile_response = chain.invoke({
            "conversation_context": conversation_context,
            "user_query": state["user_query"]
        })
        
        try:
            new_profile_info = json.loads(profile_response.content)
            # Merge with existing profile
            user_profile.update(new_profile_info)
        except json.JSONDecodeError:
            print("⚠️ Could not parse profile information")
        
        print(f"✅ Updated memory with {len(history)} messages, profile: {user_profile}")
        return {**state, "conversation_history": history, "user_profile": user_profile, "error": ""}
        
    except Exception as e:
        print(f"❌ Error updating memory: {e}")
        return {**state, "error": f"Failed to update memory: {str(e)}"}

def finalize_memory_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Add the AI response to conversation history and finalize the memory."""
    try:
        print(f"💾 Finalizing memory with AI response")
        
        # Get current conversation history
        history = state.get("conversation_history", [])
        
        # Add the AI response to history
        history.append(AIMessage(content=state["response"]))
        
        # Keep only the last 20 messages to prevent memory from growing too large
        if len(history) > 20:
            history = history[-20:]
        
        print(f"✅ Finalized memory with {len(history)} total messages")
        return {**state, "conversation_history": history, "error": ""}
        
    except Exception as e:
        print(f"❌ Error finalizing memory: {e}")
        return {**state, "error": f"Failed to finalize memory: {str(e)}"}

def route_by_intent(state: CourseAdvisorState) -> str:
    """Route to different paths based on the user's intent."""
    intent = state.get("intent", "mixed")
    
    if intent == "advisory":
        return "advisory_response"
    elif intent == "specific":
        return "generate_filters"
    else:  # mixed
        return "generate_filters"

def advisory_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate advisory response without course search, using conversation memory."""
    try:
        print(f"💡 Generating advisory response for intent: {state['intent']}")
        
        # Get conversation history and user profile
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 6 exchanges for context)
        recent_history = history[-12:] if len(history) > 12 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Create an advisory-focused prompt template with memory
        advisory_prompt = ChatPromptTemplate.from_template("""
You are **Classify**, an AI peer-advisor that helps Columbia students with academic and career guidance.

## User Profile
{user_profile}

## Recent Conversation History
{conversation_context}

## Your Mission
Provide thoughtful, personalized advice for Columbia students on:
- Academic planning and major/minor decisions
- Career preparation and professional development
- Graduate school preparation
- Research opportunities and academic involvement
- Time management and work-life balance
- Networking and extracurricular activities

## Guidelines
1. **Use the conversation history** to provide continuity and build on previous advice
2. **Reference the user profile** to personalize your recommendations
3. **Be specific to Columbia's context** - reference Columbia's resources, programs, and opportunities
4. **Consider the student's stage** - whether they're a first-year, sophomore, junior, or senior
5. **Provide actionable steps** - give concrete next steps they can take
6. **Use friendly, encouraging tone** - like a knowledgeable upperclassman giving advice
7. **Keep responses under ≈300 words** unless they ask for more detail
8. **Format with bullet points (•) and bold text** for key points

## Constraints
- Focus on general advice and guidance, not specific course recommendations
- If they ask about specific courses, suggest they ask a follow-up question about course recommendations
- Don't fabricate specific Columbia programs or resources you're unsure about
- Build on previous conversation context when relevant

CURRENT USER QUERY: {user_query}

Please provide your advisory response:
""")
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.7
        )
        
        # Create the chain
        chain = advisory_prompt | llm
        
        # Generate response
        response = chain.invoke({
            "user_query": state["user_query"],
            "conversation_context": conversation_context,
            "user_profile": json.dumps(user_profile, indent=2)
        })
        
        print(f"✅ Generated advisory response")
        return {**state, "response": response.content, "error": ""}
        
    except Exception as e:
        print(f"❌ Error generating advisory response: {e}")
        return {**state, "response": f"I encountered an error while generating advisory guidance: {str(e)}", "error": str(e)}

def generate_response_node(state: CourseAdvisorState) -> CourseAdvisorState:
    """Generate the final response using the conversational agent template with memory."""
    try:
        if state.get("error"):
            return {**state, "response": f"I encountered an error: {state['error']}. Please try rephrasing your query."}
        
        if not state.get("course_results"):
            return {**state, "response": "I couldn't find any courses matching your criteria. Please try broadening your search or rephrasing your query."}
        
        # Get conversation history and user profile
        history = state.get("conversation_history", [])
        user_profile = state.get("user_profile", {})
        
        # Prepare conversation context (last 6 exchanges for context)
        recent_history = history[-12:] if len(history) > 12 else history
        conversation_context = "\n".join([f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in recent_history])
        
        # Choose prompt template based on intent
        if state.get("intent") == "mixed":
            # Mixed intent: combine advisory guidance with course recommendations
            prompt_template = ChatPromptTemplate.from_template("""
You are **Classify**, an AI peer-advisor that helps Columbia students with both academic guidance and course recommendations.

## User Profile
{user_profile}

## Recent Conversation History
{conversation_context}

## Your Mission
1. **Provide broader academic/career advice** related to the user's query
2. **Parse the course objects in COURSE_INFO** and suggest relevant courses
3. **Connect the courses to the broader advice** - explain how these courses fit into their goals
4. **Offer actionable next steps** that combine both guidance and course planning

## Guidelines
- **Use conversation history** to provide continuity and build on previous advice
- **Reference the user profile** to personalize your recommendations
- Start with **broader advice** about their academic/career path
- Then **introduce relevant courses** that support that path
- **Explain the connection** between the advice and the courses
- Use **friendly, encouraging tone** like a knowledgeable upperclassman
- Format with **bullet points (•)** and **bold text** for key points
- Keep responses under **≈350 words**

## Course Information
COURSE_INFO:
{course_info}

CURRENT USER QUERY: {user_query}

Please provide your mixed advisory and course recommendation response:
""")
        else:
            # Specific intent: focus on course recommendations
            prompt_template = ChatPromptTemplate.from_template("""
You are **Classify**, an AI peer-advisor that helps Columbia students compare and choose classes.

## User Profile
{user_profile}

## Recent Conversation History
{conversation_context}

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

## Guidelines
- **Use conversation history** to provide continuity and build on previous advice
- **Reference the user profile** to personalize your recommendations
- **Do not** output the raw COURSE_INFO block.
- Rely only on the courses provided; if the user asks about something else, politely say you only have those courses right now.
- Keep responses under **≈250 words** unless the user explicitly asks for more detail.
- Never fabricate prerequisites, meeting times, or professor names.

COURSE_INFO:
{course_info}

CURRENT USER QUERY: {user_query}

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
            "user_query": state["user_query"],
            "conversation_context": conversation_context,
            "user_profile": json.dumps(user_profile, indent=2)
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
    workflow.add_node("update_memory", update_memory_node)
    workflow.add_node("intent_classification", intent_classification_node)
    workflow.add_node("generate_filters", generate_filters_node)
    workflow.add_node("search_courses", search_courses_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("advisory_response", advisory_response_node)
    workflow.add_node("finalize_memory", finalize_memory_node)
    
    # Add edges with conditional routing
    workflow.add_edge(START, "update_memory")
    workflow.add_edge("update_memory", "intent_classification")
    
    # Conditional routing based on intent
    workflow.add_conditional_edges(
        "intent_classification",
        route_by_intent,
        {
            "advisory_response": "advisory_response",
            "generate_filters": "generate_filters"
        }
    )
    
    # Course search path
    workflow.add_edge("generate_filters", "search_courses")
    workflow.add_edge("search_courses", "generate_response")
    
    # Finalize memory before ending
    workflow.add_edge("generate_response", "finalize_memory")
    workflow.add_edge("advisory_response", "finalize_memory")
    
    # End points
    workflow.add_edge("finalize_memory", END)
    
    # Compile the graph
    return workflow.compile()

def run_course_advisor(user_query: str, conversation_state: Dict[str, Any] = None) -> tuple[str, Dict[str, Any]]:
    """
    Run the complete course advisor workflow with memory.
    
    Args:
        user_query: The user's natural language query about courses
        conversation_state: Previous conversation state for memory continuity
    
    Returns:
        Tuple of (AI response, updated conversation state)
    """
    # Create the graph
    graph = create_course_advisor_graph()
    
    # Initialize state with memory if provided
    if conversation_state:
        initial_state = {
            "user_query": user_query,
            "intent": "mixed", # Will be updated by intent classification
            "filters": {},
            "course_results": [],
            "course_info_json": "",
            "response": "",
            "error": "",
            "conversation_history": conversation_state.get("conversation_history", []),
            "user_profile": conversation_state.get("user_profile", {})
        }
    else:
        initial_state = {
            "user_query": user_query,
            "intent": "mixed", # Default to mixed
            "filters": {},
            "course_results": [],
            "course_info_json": "",
            "response": "",
            "error": "",
            "conversation_history": [], # Initialize memory
            "user_profile": {} # Initialize user profile
        }
    
    # Run the graph
    print(f"\n🚀 Starting course advisor workflow for: '{user_query}'")
    result = graph.invoke(initial_state)
    
    # Return response and updated state for next interaction
    return result["response"], {
        "conversation_history": result["conversation_history"],
        "user_profile": result["user_profile"]
    }

def interactive_course_advisor():
    """Run an interactive version of the course advisor with persistent memory."""
    print("🎓 AI Course Advisor - Columbia University")
    print("Type 'exit' or 'quit' to end the conversation")
    print("Type 'clear' to reset conversation memory")
    print("Type 'profile' to see your current profile")
    print()
    
    # Initialize conversation state
    conversation_state = {
        "conversation_history": [],
        "user_profile": {}
    }
    
    while True:
        user_query = input("You: ").strip()
        
        if user_query.lower() in ["exit", "quit"]:
            print("👋 Goodbye! Good luck with your course selection!")
            break
        
        if user_query.lower() == "clear":
            conversation_state = {
                "conversation_history": [],
                "user_profile": {}
            }
            print("🧹 Conversation memory cleared!")
            continue
        
        if user_query.lower() == "profile":
            profile = conversation_state.get("user_profile", {})
            if profile:
                print("📋 Your current profile:")
                for key, value in profile.items():
                    print(f"  • {key}: {value}")
            else:
                print("📋 No profile information collected yet.")
            continue
        
        if not user_query:
            print("Please enter a query about courses.")
            continue
        
        try:
            response, conversation_state = run_course_advisor(user_query, conversation_state)
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