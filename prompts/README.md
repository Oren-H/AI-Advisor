# Prompt Management System

This directory contains all the prompt templates used by the AI Advisor system. The prompts are organized by functionality and can be easily modified without changing the Python code.

## Prompt Files

### Core Conversation Prompts

- **`profile_extraction.txt`** - Extracts user profile information from conversations
- **`intent_classification.txt`** - Classifies user intent (specific, advisory, mixed)
- **`advisory_response.txt`** - Generates advisory responses for academic guidance
- **`mixed_response.txt`** - Combines advisory guidance with course recommendations
- **`specific_response.txt`** - Focuses on specific course recommendations

### Filter Generation Prompts

- **`filter_generation.txt`** - Extracts structured information from user queries for course filtering
- **`department_mapping.txt`** - Maps department names to Columbia University department codes

## Usage

The prompts are managed by the `PromptManager` class in `app/prompt_manager.py`. This system provides:

- **Caching**: Prompts are loaded once and cached in memory
- **Formatting**: Easy variable substitution using Python's string formatting
- **Error handling**: Clear error messages if prompt files are missing

### Example Usage

```python
from app.prompt_manager import prompt_manager

# Get a raw prompt
prompt_text = prompt_manager.get_prompt("intent_classification")

# Get a formatted prompt with variables
formatted_prompt = prompt_manager.format_prompt(
    "mixed_response",
    user_profile=profile_json,
    conversation_context=context,
    course_info=courses_json,
    user_query=query
)
```

## Adding New Prompts

1. Create a new `.txt` file in this directory
2. Use the same variable placeholders as existing prompts (e.g., `{user_query}`, `{conversation_context}`)
3. Update the Python code to use `prompt_manager.get_prompt("your_prompt_name")`

## Benefits

- **Separation of Concerns**: Prompts are separate from logic
- **Easy Editing**: Non-technical users can modify prompts without touching code
- **Version Control**: Prompt changes are tracked in git
- **Reusability**: Common prompt patterns can be shared across functions
- **Testing**: Prompts can be tested independently of the application logic 