# Project Structure & Organization

## Root Directory Layout

```
AI-Advisor/
├── app/                    # Core application modules
├── data/                   # Course data and vector database
├── frontend/               # React TypeScript frontend
├── prompts/                # LLM prompt templates
├── scraping/               # Course data scraping tools
├── scripts/                # Utility and startup scripts
├── tests/                  # Test suite
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── requirements_api.txt    # API-specific dependencies
├── setup.py               # Package configuration
└── start_dev.sh           # Development startup script
```

## Core Application (`app/`)

### Database Operations
- `app/db_building/`: Vector database construction and management
- `app/db_querying/`: Course search, filtering, and query execution
  - `department_codes.py`: Columbia University department code mappings
  - `generate_filters.py`: Natural language to structured filter conversion
  - `query_courses_from_filter.py`: Course search execution

### Conversational AI (`app/graph/`)
- `graph_builder.py`: Full LangGraph workflow construction
- `simpler_graph_builder.py`: Simplified workflow for production
- `nodes.py`: Individual workflow nodes (intent classification, search, response)
- `simplified_nodes.py`: Streamlined node implementations
- `memory_nodes.py`: Conversation memory and user profile management
- `state_schema.py`: TypedDict definitions for workflow state
- `conversation_utils.py`: Conversation history utilities

### API & Core Services
- `api.py`: FastAPI application with REST endpoints
- `llm_manager.py`: Language model interaction management
- `prompt_manager.py`: Prompt template loading and management

### Utilities
- `app/utils/timed_step.py`: Performance monitoring utilities

## Frontend Application (`frontend/`)

### Source Code (`frontend/src/`)
- `App.tsx`: Main application component
- `main.tsx`: Application entry point
- `types.ts`: TypeScript type definitions

### Components (`frontend/src/components/`)
- `ChatBubble.tsx`: Individual message display
- `InputBar.tsx`: User input interface
- `MessageList.tsx`: Conversation history display
- `StreamingText.tsx`: Real-time text streaming

### API Integration (`frontend/src/api/`)
- `chat.ts`: Backend API communication

### Hooks (`frontend/src/hooks/`)
- `useChat.ts`: Chat state management and API integration

### Configuration
- `package.json`: Dependencies and scripts
- `vite.config.ts`: Build tool configuration
- `tailwind.config.js`: CSS framework configuration
- `tsconfig.json`: TypeScript configuration

## Data Management (`data/`)

### Course Data
- `2025-Spring.csv`: Raw course data
- `2025-Spring.json`: Processed course data
- `Cleaned Columbia Courses.csv`: Cleaned course dataset
- `Columbia Courses Final.csv`: Final processed dataset

### Vector Database (`data/chroma_db/`)
- ChromaDB persistent storage for course embeddings
- Indexed course descriptions and metadata

## Prompt Engineering (`prompts/`)

### Prompt Templates
- `advisory_response.txt`: General academic advisory responses
- `filter_generation.txt`: Natural language to filter conversion
- `intent_classification.txt`: Query intent classification
- `mixed_response.txt`: Combined search and advisory responses
- `profile_extraction.txt`: User profile extraction from conversations
- `specific_response.txt`: Specific course search responses

## Testing (`tests/`)

### Test Categories
- `test_api.py`: FastAPI endpoint testing
- `test_course_advisor.py`: End-to-end conversation testing
- `test_functions.py`: Individual function unit tests
- `test_modular_structure.py`: Module integration testing
- `test_prompt_manager.py`: Prompt management testing
- `scraper_tester.py`: Web scraping functionality testing

## Scripts (`scripts/`)

### Utility Scripts
- `run_api.py`: FastAPI server startup
- `graph_runner.py`: Standalone graph execution
- `manage_prompts.py`: Prompt template management

## Web Scraping (`scraping/`)

### Data Collection
- `columbia_course_scraper.py`: Course catalog scraping
- `main.ipynb`: Jupyter notebook for data exploration

## Naming Conventions

### Python Files
- Snake_case for file names and functions
- PascalCase for class names
- ALL_CAPS for constants
- Descriptive module names indicating functionality

### TypeScript/React Files
- PascalCase for component files
- camelCase for utility functions and hooks
- kebab-case for CSS classes (Tailwind)

### Directory Structure
- Logical grouping by functionality
- Clear separation between frontend and backend
- Dedicated directories for data, tests, and utilities

## Import Patterns

### Python Imports
```python
# Standard library first
from typing import Dict, List, Optional

# Third-party libraries
from fastapi import FastAPI
from langchain.schema import HumanMessage

# Local imports
from app.graph.state_schema import CourseAdvisorState
```

### TypeScript Imports
```typescript
// React and external libraries
import React from 'react';
import { useState } from 'react';

// Local components and utilities
import { ChatBubble } from './components/ChatBubble';
import { useChat } from './hooks/useChat';
```

## Configuration Files

### Environment Management
- `.env`: Local environment variables
- `frontend/.env`: Frontend-specific variables
- `frontend/env.example`: Template for environment setup

### Package Management
- `requirements.txt`: Full Python dependencies
- `requirements_api.txt`: Minimal API dependencies
- `frontend/package.json`: Node.js dependencies and scripts