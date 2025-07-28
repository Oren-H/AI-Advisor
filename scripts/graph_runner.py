import os
from typing import Dict, Any, Tuple
from graph_builder import create_course_advisor_graph
from database_utils import load_vector_database

def run_course_advisor(user_query: str, conversation_state: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
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

def main():
    """Main entry point for the course advisor."""
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

if __name__ == "__main__":
    main() 