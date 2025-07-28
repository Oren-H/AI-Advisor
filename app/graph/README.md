# Course Advisor Graph Module

This module implements an intelligent course recommendation system using LangGraph for conversational AI.

## Purpose

The `graph` module provides:
- A conversational AI agent for course recommendations
- Memory management for user preferences and conversation history
- Intent classification and routing
- Structured course search and response generation

## Architecture

The module uses a modular LangGraph architecture with separate components for different functionalities:

### Core Components

#### `state_schema.py`
Defines the conversation state structure using TypedDict.

**Key Components:**
- `CourseAdvisorState`: Main state schema with conversation history and user profile

#### `nodes.py`
Contains all non-memory related nodes for the conversation flow.

**Key Nodes:**
- `intent_classification_node`: Classifies user intent (specific, advisory, mixed)
- `generate_filters_node`: Converts user queries to database filters
- `search_courses_node`: Searches for courses using vector and metadata filtering
- `advisory_response_node`: Generates advisory responses without course search
- `generate_response_node`: Creates final responses with course recommendations
- `route_by_intent`: Routes conversation based on user intent

#### `memory_nodes.py`
Handles conversation memory and user profile management.

**Key Nodes:**
- `update_memory_node`: Updates conversation memory and extracts user preferences
- `finalize_memory_node`: Finalizes memory with AI responses

#### `graph_builder.py`
Constructs the LangGraph workflow and defines node connections.

**Key Functions:**
- `create_course_advisor_graph()`: Builds and compiles the complete graph

#### `graph_runner.py`
Provides execution logic and interactive interfaces.

**Key Functions:**
- `run_course_advisor()`: Runs single queries
- `interactive_course_advisor()`: Interactive mode with persistent memory
- `main()`: Entry point for the application

## Workflow

```
START
  ↓
update_memory_node (extract user preferences)
  ↓
intent_classification_node (classify query type)
  ↓
route_by_intent (route to appropriate path)
  ↓
├─ advisory_response_node (general advice) ──┐
└─ generate_filters_node (course search)     │
  ↓                                           │
search_courses_node (find courses)           │
  ↓                                           │
generate_response_node (recommendations) ────┘
  ↓
finalize_memory_node (update conversation)
  ↓
END
```

## Usage

### Interactive Mode
```bash
python graph_runner.py
```

### Programmatic Usage
```python
from graph_runner import run_course_advisor

# Run a single query
response = run_course_advisor("I need computer science classes in the morning")
```

### Example Conversations

**Course Search:**
- User: "Show me computer science classes on Mondays and Wednesdays"
- System: Searches database and returns relevant courses

**Advisory:**
- User: "What should I take as a CS major?"
- System: Provides general advice about course selection

**Mixed Intent:**
- User: "I'm interested in AI and want classes in the afternoon"
- System: Combines advisory guidance with specific course search

## Features

- **Memory Management**: Remembers user preferences and conversation history
- **Intent Classification**: Distinguishes between course search and advisory requests
- **Structured Search**: Combines semantic and metadata-based filtering
- **Conversational Flow**: Natural back-and-forth dialogue
- **User Profile Building**: Gradually learns user preferences over time

## Dependencies

- `langgraph` for workflow orchestration
- `langchain_openai` for LLM integration
- `chromadb` for vector database queries
- `pydantic` for data validation 