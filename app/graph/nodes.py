import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage

# Import our existing modules using absolute imports
from app.db_querying.generate_filters import generate_filters_from_prompt
from app.db_querying.query_courses_from_filter import query_courses_with_filters
from app.graph.state_schema import CourseAdvisorState

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

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

def route_by_intent(state: CourseAdvisorState) -> str:
    """Route to different paths based on the user's intent."""
    intent = state.get("intent", "mixed")
    
    if intent == "advisory":
        return "advisory_response"
    elif intent == "specific":
        return "generate_filters"
    else:  # mixed
        return "generate_filters" 