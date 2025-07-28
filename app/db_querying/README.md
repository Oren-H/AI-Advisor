# Database Querying Module

This module handles querying and filtering course data from the vector database.

## Purpose

The `db_querying` module is responsible for:
- Generating structured filters from natural language queries
- Mapping department names to department codes
- Executing semantic and metadata-based searches
- Providing course recommendations based on user preferences

## Files

### `generate_filters.py`
Core module for converting natural language queries into structured database filters.

**Key Functions:**
- `generate_filters_from_prompt()`: Main function that processes user queries
- `map_department_to_code()`: Maps department names to Columbia University codes
- `build_chroma_filters()`: Converts structured queries to Chroma filter format
- `get_text_query_from_prompt()`: Extracts text for semantic search

**Features:**
- Uses GPT-4 to extract structured information from natural language
- Handles time preferences (mornings, afternoons, evenings)
- Maps department names to official Columbia codes
- Supports credit, day, and course type filtering

### `query_courses_from_filter.py`
Executes database queries using generated filters and returns course recommendations.

**Key Functions:**
- `query_courses()`: Main function for searching courses
- Combines vector search with metadata filtering
- Returns ranked course results with relevance scores

### `department_codes.py`
Contains mapping of Columbia University department names to their official codes.

**Key Components:**
- `dept_codes`: Dictionary mapping department names to codes
- Used by the filter generation system for accurate department matching

## Usage

```python
from generate_filters import generate_filters_from_prompt
from query_courses_from_filter import query_courses

# Generate filters from natural language
user_query = "I want computer science classes in the morning on Mondays and Wednesdays"
filters = generate_filters_from_prompt(user_query)

# Query courses with filters
courses = query_courses(filters)
```

## Supported Query Types

- **Department/Subject**: "computer science", "math", "literature"
- **Time Preferences**: "mornings", "afternoons", "evenings", "before 9 PM"
- **Days**: "Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays"
- **Credits**: Specific credit amounts
- **Course Types**: "lecture", "seminar", "lab", "recitation"

## Dependencies

- `langchain_openai.ChatOpenAI`
- `pydantic` for structured data validation
- `chromadb` for vector database queries 