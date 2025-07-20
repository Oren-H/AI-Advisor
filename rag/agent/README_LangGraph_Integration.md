# Course Advisor LangGraph Integration

This document describes the LangGraph-based integration that connects the filter generation, vector search, and conversational agent components into a unified course recommendation system.

## Overview

The system uses LangGraph to orchestrate three main components:

1. **Filter Generation** (`generate_filters.py`) - Extracts metadata filters from natural language queries
2. **Vector Search** (`query_courses.py`) - Searches the course database using the generated filters
3. **Conversational Agent** (`conversational_agent.py`) - Provides AI-powered course recommendations and advice

## Architecture

```
User Query → LangGraph Workflow
    ↓
1. Generate Filters Node
    ↓
2. Search Courses Node  
    ↓
3. Generate Response Node
    ↓
AI Course Advisor Response
```

## Files

- `course_advisor_graph.py` - Main LangGraph implementation
- `test_course_advisor.py` - Test script for the integration
- `generate_filters.py` - Filter generation module (renamed from `generate_filters`)
- `query_courses.py` - Vector search module
- `conversational_agent.py` - AI advisor module

## Usage

### Interactive Mode

Run the interactive course advisor:

```bash
cd rag
python course_advisor_graph.py
```

### Programmatic Usage

```python
from course_advisor_graph import run_course_advisor

# Get course recommendations
response = run_course_advisor("Find me computer science courses with 3 credits")
print(response)
```

### Testing

Run the test suite:

```bash
cd rag
python test_course_advisor.py
```

## Workflow Steps

### 1. Filter Generation Node
- Takes user's natural language query
- Uses LLM to extract structured filters (department, days, times, credits, etc.)
- Returns filter dictionary for database querying

### 2. Search Courses Node
- Uses generated filters to search the vector database
- Retrieves top-k most relevant courses
- Converts results to JSON format for the conversational agent

### 3. Generate Response Node
- Takes course results and user query
- Uses the conversational agent template to generate helpful advice
- Provides course comparisons, recommendations, and next steps

## State Management

The LangGraph uses a `CourseAdvisorState` TypedDict to manage data flow:

```python
class CourseAdvisorState(TypedDict):
    user_query: str          # Original user query
    filters: Dict[str, Any]  # Generated metadata filters
    course_results: List[Dict[str, Any]]  # Retrieved courses
    course_info_json: str    # JSON string for LLM
    response: str           # Final AI response
    error: str             # Error messages
```

## Error Handling

- Each node includes try-catch blocks for robust error handling
- Errors are propagated through the state
- The response node provides user-friendly error messages

## Dependencies

Make sure to install the required packages:

```bash
pip install -r requirements.txt
```

The system requires:
- `langgraph>=0.0.20` (newly added)
- Existing LangChain ecosystem packages
- Vector database (Chroma) with course data

## Example Queries

The system can handle various types of queries:

- "Find me computer science courses with 3 credits"
- "Show me machine learning courses offered on Tuesday"
- "What math courses are available for beginners?"
- "Find courses in the psychology department"
- "I need a course that meets on Monday and Wednesday after 2 PM"

## Benefits of LangGraph Integration

1. **Modularity** - Each component can be developed and tested independently
2. **Observability** - Clear workflow steps with logging and state tracking
3. **Extensibility** - Easy to add new nodes or modify the workflow
4. **Error Handling** - Robust error propagation and recovery
5. **State Management** - Structured data flow between components

## Future Enhancements

Potential improvements to consider:

1. **Conditional Routing** - Add decision nodes for different query types
2. **Memory** - Add conversation history to the state
3. **Tool Integration** - Add external tools for course registration, etc.
4. **Multi-turn Conversations** - Support for follow-up questions
5. **Personalization** - Include user preferences in the state 