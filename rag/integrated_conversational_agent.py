import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from query_courses import query_courses_with_filters

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Create the prompt template
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
- If no courses are found, suggest alternative search terms or ask for clarification.

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

# Create the chain using RunnableSequence (newer approach)
chain = prompt_template | llm

def get_courses_for_query(user_query: str, k: int = 5) -> str:
    """
    Get course information for a user query.
    
    Args:
        user_query: The user's natural language query
        k: Number of courses to return
    
    Returns:
        JSON string with course information
    """
    try:
        return query_courses_with_filters(user_query, k)
    except Exception as e:
        print(f"Error fetching courses: {e}")
        return json.dumps([])

def is_course_search_query(user_query: str) -> bool:
    """
    Determine if the user query is asking for course information.
    
    Args:
        user_query: The user's query
    
    Returns:
        True if the query is asking for course information
    """
    # Keywords that indicate course search
    course_keywords = [
        "course", "class", "find", "show", "search", "look", "recommend",
        "suggest", "what", "which", "department", "major", "subject",
        "machine learning", "calculus", "computer science", "math",
        "physics", "chemistry", "biology", "economics", "history",
        "english", "philosophy", "psychology", "sociology", "art",
        "music", "drama", "film", "writing", "language"
    ]
    
    query_lower = user_query.lower()
    return any(keyword in query_lower for keyword in course_keywords)

def main():
    """
    Main conversation loop for the integrated course advisor.
    """
    print("🎓 Columbia Course Advisor - AI Peer Advisor")
    print("=" * 50)
    print("I can help you find and compare Columbia courses!")
    print("Type 'exit' or 'quit' to end the conversation")
    print("=" * 50)
    print()

    while True:
        user_query = input("You: ")
        
        if user_query.strip().lower() in ["exit", "quit"]:
            print("Thanks for using the Columbia Course Advisor! Good luck with your course selection!")
            break

        try:
            # Check if this is a course search query
            if is_course_search_query(user_query):
                print("🔍 Searching for courses...")
                
                # Get course information
                course_info_json = get_courses_for_query(user_query, k=5)
                courses = json.loads(course_info_json)
                
                if not courses:
                    print("❌ No courses found matching your criteria.")
                    print("💡 Try different keywords or be more specific about what you're looking for.")
                    print("   Examples:")
                    print("   - 'Find computer science courses'")
                    print("   - 'Show me calculus classes in the math department'")
                    print("   - 'What machine learning courses are available?'")
                    print()
                    continue
                
                print(f"✅ Found {len(courses)} course{'s' if len(courses) != 1 else ''}!")
                print()
                
                # Run the conversational chain
                response = chain.invoke({
                    "course_info": course_info_json,
                    "user_query": user_query
                })
                
                print(f"AI: {response.content}\n")
                
            else:
                # Handle non-course queries
                print("🤔 I'm designed to help with course selection and academic planning.")
                print("💡 Try asking about specific courses, departments, or academic subjects.")
                print("   Examples:")
                print("   - 'Find me a machine learning course'")
                print("   - 'What calculus courses are available?'")
                print("   - 'Show me computer science courses with 3 credits'")
                print("   - 'Find courses in the math department offered on Tuesdays'")
                print()
        
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again with a different query.\n")

if __name__ == "__main__":
    main() 