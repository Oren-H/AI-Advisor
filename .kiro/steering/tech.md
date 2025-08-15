# Technology Stack & Build System

## Backend Stack

### Core Framework
- **Python 3.8+**: Primary backend language
- **FastAPI**: REST API framework with automatic OpenAPI documentation
- **Uvicorn**: ASGI server for FastAPI applications
- **Pydantic**: Data validation and serialization

### AI & ML Components
- **LangChain**: Framework for building LLM applications
- **LangGraph**: Workflow orchestration for conversational AI
- **OpenAI API**: Large language model for natural language processing
- **ChromaDB**: Vector database for semantic search
- **FAISS**: Alternative vector search library

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Scikit-learn**: Machine learning utilities

### Web Scraping
- **Playwright**: Browser automation for course data scraping
- **BeautifulSoup4**: HTML parsing
- **Requests**: HTTP client library

## Frontend Stack

### Core Framework
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool and development server

### UI & Styling
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
- **React Markdown**: Markdown rendering component

### Development Tools
- **ESLint**: Code linting
- **PostCSS**: CSS processing
- **Autoprefixer**: CSS vendor prefixing

## Development Environment

### Virtual Environment
```bash
# Create and activate Python virtual environment
python3 -m venv rag_env
source rag_env/bin/activate  # macOS/Linux
```

### Backend Setup
```bash
# Install API dependencies
pip install -r requirements_api.txt

# Install full project dependencies
pip install -r requirements.txt

# Start development server
python scripts/run_api.py
# or
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Common Commands

### Development
```bash
# Start both backend and frontend
./start_dev.sh

# Backend only
python scripts/run_api.py

# Frontend only (from frontend directory)
npm run dev
```

### Testing
```bash
# Run API tests
python tests/test_api.py

# Run all tests
python -m pytest tests/

# Frontend tests (from frontend directory)
npm test
```

### Building
```bash
# Frontend production build
cd frontend
npm run build

# Python package installation
pip install -e .
```

### Data Management
```bash
# Update course data
python scraping/columbia_course_scraper.py

# Rebuild vector database
python app/db_building/build_vector_db.py
```

## Environment Variables

### Backend
- `OPENAI_API_KEY`: Required for LLM functionality
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `RELOAD`: Enable auto-reload for development

### Frontend
- `VITE_API_URL`: Backend API endpoint (default: http://localhost:8000)

## Architecture Patterns

- **Modular Design**: Separate modules for database operations, graph workflows, and API endpoints
- **State Management**: LangGraph state schema for conversation flow
- **Memory Management**: Conversation history and user profile persistence
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **CORS Configuration**: Configured for cross-origin requests from frontend