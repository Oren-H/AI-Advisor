# Course Advisor Graph - Modular Structure

This document describes the modular structure of the course advisor graph, which has been split into separate files for better organization and maintainability.

## File Structure

### 1. `state_schema.py`
**Purpose**: Contains the state schema class definition
- Defines the `CourseAdvisorState` TypedDict class
- Contains all the fields that make up the state of the conversation
- Includes conversation history and user profile for memory management

**Key Components**:
- `CourseAdvisorState`: The main state schema with all required fields

### 2. `nodes.py`
**Purpose**: Contains all nodes that don't deal with memory
- Intent classification node
- Filter generation node
- Course search node
- Response generation nodes (both advisory and course-specific)
- Routing logic

**Key Components**:
- `intent_classification_node`: Classifies user intent (specific, advisory, mixed)
- `generate_filters_node`: Generates metadata filters from user query
- `search_courses_node`: Searches for courses using filters and vector search
- `advisory_response_node`: Generates advisory responses without course search
- `generate_response_node`: Generates final responses with course recommendations
- `route_by_intent`: Routes to different paths based on user intent

### 3. `memory_nodes.py`
**Purpose**: Contains all nodes that deal with memory management
- Memory update node
- Memory finalization node

**Key Components**:
- `update_memory_node`: Updates conversation memory and extracts user profile information
- `finalize_memory_node`: Adds AI response to conversation history and finalizes memory

### 4. `graph_builder.py`
**Purpose**: Contains the graph building logic and workflow definition
- Creates the LangGraph workflow
- Defines node connections and conditional routing
- Compiles the final graph

**Key Components**:
- `create_course_advisor_graph()`: Main function that builds and compiles the graph

### 5. `graph_runner.py`
**Purpose**: Contains logic for running the built graph
- Main execution function
- Interactive course advisor
- State management and initialization

**Key Components**:
- `run_course_advisor()`: Runs the complete workflow with memory
- `interactive_course_advisor()`: Interactive version with persistent memory
- `main()`: Entry point for the application

### 6. `course_advisor_graph.py` (Updated)
**Purpose**: Legacy compatibility file
- Now simply imports and calls the modular components
- Maintains backward compatibility with existing code

## Workflow Overview

```
START
  ↓
update_memory_node (memory_nodes.py)
  ↓
intent_classification_node (nodes.py)
  ↓
route_by_intent (nodes.py)
  ↓
├─ advisory_response_node (nodes.py) ──┐
└─ generate_filters_node (nodes.py)     │
  ↓                                     │
search_courses_node (nodes.py)          │
  ↓                                     │
generate_response_node (nodes.py) ──────┘
  ↓
finalize_memory_node (memory_nodes.py)
  ↓
END
```

## Usage

### Running the Interactive Advisor
```bash
python course_advisor_graph.py
```

### Using the Modular Components
```python
from graph_runner import run_course_advisor

# Run a single query
response, conversation_state = run_course_advisor("What CS courses should I take?")

# Continue conversation with memory
response, conversation_state = run_course_advisor("Tell me more about algorithms", conversation_state)
```

### Testing the Structure
```bash
python test_modular_structure.py
```

## Benefits of Modular Structure

1. **Separation of Concerns**: Each file has a specific responsibility
2. **Maintainability**: Easier to modify individual components
3. **Testability**: Can test each module independently
4. **Reusability**: Components can be reused in different contexts
5. **Readability**: Code is more organized and easier to understand
6. **Scalability**: Easier to add new features or modify existing ones

## Dependencies

Each module imports only what it needs:
- `state_schema.py`: Only imports typing and langchain schema
- `nodes.py`: Imports langchain components and existing modules
- `memory_nodes.py`: Imports langchain components and state schema
- `graph_builder.py`: Imports langgraph and node functions
- `graph_runner.py`: Imports graph builder and database utils

## Migration Notes

The original `course_advisor_graph.py` file has been updated to maintain backward compatibility. All existing functionality is preserved, but the code is now organized into logical modules.

To use the new structure in existing code, simply update imports:
```python
# Old way
from course_advisor_graph import run_course_advisor

# New way
from graph_runner import run_course_advisor
``` 