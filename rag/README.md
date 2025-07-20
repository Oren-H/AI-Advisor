# Columbia Course Advisor - RAG System

This directory contains the RAG (Retrieval-Augmented Generation) system for the Columbia Course Advisor project.

## Directory Structure

### Database Components (Root Level)
- **`build_vector_db.py`** - Script to build the vector database from CSV data
- **`database_utils.py`** - Utilities for loading and managing the vector database
- **`document_embeddings.py`** - Main interface for building and querying the course database

### Agent Components (`agent/` directory)
- **`query_courses.py`** - Core querying functionality for course search
- **`course_advisor_graph.py`** - LangGraph-based workflow for course advising
- **`generate_filters.py`** - Natural language to filter conversion
- **`conversational_agent.py`** - Simple conversational interface
- **`department_codes.py`** - Department code mappings
- **`test_course_advisor.py`** - Test suite for the agent components
- **`README.md`** - Documentation for agent components
- **`README_LangGraph_Integration.md`** - LangGraph-specific documentation

## Usage

### Setting up the Database
```bash
# Activate the virtual environment
source rag_env/bin/activate

# Build the vector database (only needed once or when data changes)
python build_vector_db.py
```

### Running the Agent Components
```bash
# Navigate to the agent directory
cd agent

# Test the course advisor
python test_course_advisor.py

# Run the conversational agent
python conversational_agent.py
```

## Virtual Environment

The project uses a virtual environment located at `../rag_env/`. Make sure to activate it before running any scripts:

```bash
source rag_env/bin/activate
```

## Database Location

The vector database is stored in `../chroma_db/` relative to this directory. 