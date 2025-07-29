import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.prompt_manager import prompt_manager

def test_prompt_manager():
    """Test the prompt manager functionality."""
    print("🧪 Testing Prompt Manager...")
    
    # Test listing available prompts
    available_prompts = prompt_manager.list_available_prompts()
    print(f"✅ Available prompts: {available_prompts}")
    
    # Test getting a prompt
    try:
        intent_prompt = prompt_manager.get_prompt("intent_classification")
        print(f"✅ Successfully loaded intent_classification prompt ({len(intent_prompt)} characters)")
    except FileNotFoundError as e:
        print(f"❌ Failed to load intent_classification prompt: {e}")
        return False
    
    # Test formatting a prompt
    try:
        formatted_prompt = prompt_manager.format_prompt(
            "intent_classification",
            user_profile="{}",
            conversation_context="Test conversation",
            user_query="What CS courses should I take?"
        )
        print(f"✅ Successfully formatted intent_classification prompt ({len(formatted_prompt)} characters)")
    except Exception as e:
        print(f"❌ Failed to format intent_classification prompt: {e}")
        return False
    
    # Test caching
    prompt1 = prompt_manager.get_prompt("intent_classification")
    prompt2 = prompt_manager.get_prompt("intent_classification")
    if prompt1 is prompt2:  # Should be the same object due to caching
        print("✅ Prompt caching is working correctly")
    else:
        print("❌ Prompt caching is not working")
        return False
    
    print("🎉 All prompt manager tests passed!")
    return True

if __name__ == "__main__":
    test_prompt_manager() 