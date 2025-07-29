#!/usr/bin/env python3
"""
Utility script for managing prompts in the AI Advisor system.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.prompt_manager import prompt_manager

def list_prompts():
    """List all available prompts with their sizes."""
    print("📋 Available Prompts:")
    print("-" * 50)
    
    available_prompts = prompt_manager.list_available_prompts()
    
    for prompt_name in sorted(available_prompts):
        try:
            prompt_content = prompt_manager.get_prompt(prompt_name)
            size = len(prompt_content)
            print(f"📄 {prompt_name:.<30} {size:>6} chars")
        except Exception as e:
            print(f"❌ {prompt_name:.<30} ERROR: {e}")
    
    print(f"\nTotal: {len(available_prompts)} prompts")

def validate_prompts():
    """Validate that all prompts can be loaded and formatted."""
    print("🔍 Validating Prompts...")
    print("-" * 50)
    
    available_prompts = prompt_manager.list_available_prompts()
    errors = []
    
    for prompt_name in available_prompts:
        try:
            # Test loading
            prompt_content = prompt_manager.get_prompt(prompt_name)
            
            # Test basic formatting by providing all possible variables
            test_vars = {
                "user_query": "test",
                "user_profile": "{}",
                "conversation_context": "test",
                "course_info": "[]",
                "user_prompt": "test",
                "department_name": "test",
                "dept_list": "test"
            }
            
            # Only pass variables that are actually in the prompt
            required_vars = {}
            for var_name, var_value in test_vars.items():
                if f"{{{var_name}}}" in prompt_content:
                    required_vars[var_name] = var_value
            
            prompt_manager.format_prompt(prompt_name, **required_vars)
            
            print(f"✅ {prompt_name}")
            
        except Exception as e:
            print(f"❌ {prompt_name}: {e}")
            errors.append((prompt_name, str(e)))
    
    if errors:
        print(f"\n❌ Found {len(errors)} errors:")
        for prompt_name, error in errors:
            print(f"   - {prompt_name}: {error}")
        return False
    else:
        print(f"\n🎉 All {len(available_prompts)} prompts are valid!")
        return True

def show_prompt(prompt_name):
    """Show the content of a specific prompt."""
    try:
        content = prompt_manager.get_prompt(prompt_name)
        print(f"📄 {prompt_name}:")
        print("=" * 50)
        print(content)
        print("=" * 50)
    except Exception as e:
        print(f"❌ Error loading {prompt_name}: {e}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python manage_prompts.py [list|validate|show <prompt_name>]")
        print("\nCommands:")
        print("  list     - List all available prompts")
        print("  validate - Validate all prompts")
        print("  show     - Show content of a specific prompt")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_prompts()
    elif command == "validate":
        validate_prompts()
    elif command == "show":
        if len(sys.argv) < 3:
            print("❌ Please specify a prompt name to show")
            return
        prompt_name = sys.argv[2]
        show_prompt(prompt_name)
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, validate, show")

if __name__ == "__main__":
    main() 