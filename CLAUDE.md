# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

The AI Course Advisor is a conversational AI system for Columbia University course recommendations, built with a modular Python backend and React TypeScript frontend. It uses LangGraph for conversational flow, ChromaDB for vector search, and OpenAI for embeddings and language processing.

### Core Architecture

```
Frontend (React/TS) ↔ FastAPI Backend ↔ ChromaDB Vector Database
                              ↓
                      LangGraph Workflow Engine
                              ↓
                     OpenAI (Embeddings + GPT-4)
```

### Key Modules

- **`app/graph/`**: LangGraph-based conversational AI workflow with intent classification, memory management, and response generation
- **`app/db_building/`**: Vector database construction from CSV course data using OpenAI embeddings
- **`app/db_querying/`**: Natural language to database filter conversion and course search execution
- **`app/api.py`**: FastAPI server providing REST endpoints for the frontend
- **`frontend/`**: React TypeScript interface with chat functionality and streaming responses

## Development Setup

### Environment Setup
```bash
# Create and activate Python virtual environment
conda activate base
source rag_env/bin/activate  # On Windows: rag_env\Scripts\activate

# Install dependencies
pip install -r requirements_api.txt    # For API server only
pip install -r requirements.txt        # For full functionality

# Frontend setup
cd frontend
npm install
cd ..
```

### Environment Variables
Copy `frontend/env.example` to `frontend/.env` and add your OpenAI API key.

## Common Development Commands

### Starting the Application

**Method 1: Manual (Recommended)**
```bash
# Terminal 1 - Backend
conda activate base
python3 scripts/run_api.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

**Method 2: Development Script**
```bash
chmod +x start_dev.sh
./start_dev.sh
```

### Testing
```bash
# API tests (requires running backend)
python3 tests/test_api.py

# Run all tests
cd tests
python -m pytest
```

### Database Operations
```bash
# Rebuild vector database from course data
python app/db_building/build_vector_db.py

# Update course data
python scraping/columbia_course_scraper.py
```

### Frontend Commands
```bash
cd frontend
npm run dev        # Development server
npm run build      # Production build
npm run lint       # ESLint
npm run preview    # Preview production build
```

## Key Concepts

### LangGraph Workflow
The conversational AI uses a graph-based workflow:
1. **Memory Update**: Extract user preferences from conversation
2. **Intent Classification**: Determine if query is specific course search, advisory, or mixed
3. **Routing**: Direct to appropriate processing path
4. **Response Generation**: Create contextual responses with course recommendations
5. **Memory Finalization**: Update conversation history and user profile

### Vector Database Structure
- Course embeddings generated from descriptions and metadata
- Metadata includes: department, time (minutes from midnight), credits, days, course type
- Supports both semantic search and structured filtering

### Department Code Mapping
The system maps natural language department names to Columbia University codes via `app/db_querying/department_codes.py`.

### Prompt Management
All LLM prompts are stored as text files in `prompts/` and managed by `PromptManager` for easy modification without code changes.

## API Endpoints

- `GET /`: Health check
- `POST /chat`: Main conversation endpoint
- `GET /conversations`: List all conversations  
- `GET /conversations/{id}`: Get conversation details
- `GET /docs`: Interactive API documentation

## Development Notes

- The system uses ChromaDB for vector storage with persistence in `data/chroma_db/`
- Course data is loaded from CSV files in `data/` directory
- The LangGraph workflow maintains conversation state and user profiles in memory
- All time-based filtering converts to "minutes from midnight" for consistency
- The frontend uses Server-Sent Events for streaming responses from the backend

## Major Scraping Branch

The current branch includes experimental major scraping functionality in `major_scraping/` for extracting comprehensive major requirements from Columbia's website. This uses BeautifulSoup for HTML parsing and creates structured JSON data for major requirements.