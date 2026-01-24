## AI Advisor

Intelligent course-advising assistant with a FastAPI backend (LangChain + LangGraph + Chroma) and a React + TypeScript + Vite + Tailwind frontend. It ingests Columbia course data and bulletin PDFs into vector stores, and uses tool-augmented LLM reasoning to search courses, look up major/school requirements, and maintain a lightweight conversation state.

### Key Features
- Conversational advisor with streaming responses (Server-Sent Events)
- Tool-augmented agent: course search, course lookup, major and school requirement lookups
- Vector databases built from course CSV and bulletin PDF (Chroma + OpenAI embeddings)
- Minimal conversation memory keyed by conversation_id
- Production-ready React chat UI with dark mode and SSE streaming
- Structured logging with separate files for API, streaming events, and tool execution

---

## Architecture

```
AI-Advisor/
├── backend/
│   ├── app/                           # FastAPI application
│   │   ├── main.py                    # API endpoints and SSE streaming
│   │   ├── run_api.py                 # Server startup script
│   │   └── schemas.py                 # Pydantic request/response models
│   │
│   ├── agent/                         # LangGraph agent system
│   │   ├── graph/
│   │   │   ├── agent.py               # Main agent graph and tool definitions
│   │   │   ├── conversation_utils.py  # Conversation state management
│   │   │   ├── majors_summary.py      # Major requirements lookup tool
│   │   │   ├── school_requirements.py # School requirements lookup tool
│   │   │   └── old/                   # Deprecated graph implementations
│   │   │
│   │   ├── db_querying/
│   │   │   ├── generate_course_filters.py  # LLM-based filter generation
│   │   │   └── query_courses_from_filter.py # Course search execution
│   │   │
│   │   ├── prompts/                   # System prompts for agent and tools
│   │   │   ├── agent_system_prompt.txt
│   │   │   ├── filter_generation.txt
│   │   │   ├── intent_classification.txt
│   │   │   ├── plan_major.txt
│   │   │   └── profile_extraction.txt
│   │   │
│   │   ├── utils/                     # Shared utilities
│   │   ├── logs/                      # Runtime logs (API, agent, tools)
│   │   ├── database_cache.py          # Vector DB and data caching
│   │   ├── llm_manager.py             # LLM provider configuration
│   │   └── prompt_manager.py          # Prompt loading and formatting
│   │
│   ├── databases/
│   │   ├── build_course_vector_db.py  # Course vector DB builder
│   │   ├── build_bulletin_vector_db.py # Bulletin vector DB builder
│   │   ├── database_utils.py          # Shared DB utilities
│   │   ├── paths.py                   # Path configuration
│   │   ├── data/                      # Chroma DBs and source data
│   │   └── cache/                     # Cached processed data
│   │
│   ├── tests/                         # Backend tests
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── api/
│       │   └── chat.ts                # SSE client for streaming
│       ├── components/
│       │   ├── ChatBubble.tsx         # Message display component
│       │   ├── InputBar.tsx           # User input component
│       │   ├── MessageList.tsx        # Chat history display
│       │   ├── ProfileForm.tsx        # User profile setup
│       │   ├── Sidebar.tsx            # Conversation list
│       │   ├── Header.tsx             # App header
│       │   └── StreamingText.tsx      # Streaming text renderer
│       ├── hooks/
│       │   └── useChat.ts             # Chat state management hook
│       ├── pages/
│       │   └── ChatPage.tsx           # Main chat page
│       ├── App.tsx                    # Root component
│       ├── types.ts                   # TypeScript type definitions
│       └── index.css                  # Tailwind styles
│
└── columbia-catalog-scraper-master/   # Course data scraping tools
```

---

## Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- OpenAI API key (for embeddings and optionally LLMs)
- Optional: Anthropic API key (if using Anthropic chat model), TokenCrush key (for PDF chunk optimization)

---

## Quick Start

1) Backend – install and configure

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create backend/.env
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key   # optional (used by agent model)
TOKENCRUSH_API_KEY=your_tokencrush_key # optional (for bulletin chunk optimization)
HOST=0.0.0.0
PORT=8000
RELOAD=true
EOF
```

2) Build vector databases (first run only or when data changes)

- Courses (requires a CSV in `backend/databases/data/course_csv/`—default filenames are referenced in the code):
```bash
cd backend/databases
python build_course_vector_db.py
```

- Bulletin PDF:
```bash
cd backend/databases
python build_bulletin_vector_db.py
```

3) Run the API server
```bash
cd backend
python app/run_api.py
# Swagger:  http://localhost:8000/docs
# ReDoc:    http://localhost:8000/redoc
```

4) Frontend – install and run
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## Backend API

Base URL: `http://localhost:8000`

- `GET /` – Health check
  - Returns `{ status, timestamp, graph_ready }`

- `POST /chat` – Non-streaming chat
  - Body:
    ```json
    {
      "message": "Find ML classes on Tuesday",
      "conversation_id": "optional-guid",
      "user_profile": {
        "name": "Jane",
        "school": "SEAS",
        "department_of_major": "COMS",
        "major": "Computer Science",
        "completed_courses": ["COMS1004"],
        "semester": 2,
        "career_goals": ["Software Engineering"],
        "preferences": ["morning"]
      }
    }
    ```
  - Response: `{ response, conversation_id }`

- `POST /chat/stream` – Streaming chat (SSE)
  - Body: same as `/chat`
  - Stream events:
    - `{"type":"metadata","conversation_id": "..."}`
    - Repeated `{"type":"token","content": "..."}`
    - Optional tool events: `{"type":"tool"...}`, `{"type":"tool_result"...}`
    - `{"type":"end"}` when complete

- Conversation management
  - `GET /conversations` – List conversations
  - `GET /conversations/{id}` – Details and history
  - `DELETE /conversations/{id}` – Delete conversation
  - `DELETE /conversations` – Clear all
  - `GET /conversations/{id}/profile` – Get user profile
  - `PUT /conversations/{id}/profile` – Update user profile
  - `POST /profile/initialize` – Create a new conversation with profile

Notes
- On startup, the app preloads course CSV, course vector DB, bulletin docs cache, and bulletin DB if present.
- Course DB must exist; bulletin DB is optional and will be built on first use if not present.
- Streaming filters out internal tool LLM calls (e.g., filter generation) to only show final agent responses to users.

---

## Frontend

- Dev server: `npm run dev` (defaults to port 3000)
- Config: `VITE_API_URL` (defaults to `http://localhost:8000`)
- Source: `frontend/src`
  - API integration: `src/api/chat.ts` (SSE client)
  - Hooks: `src/hooks/useChat.ts`
  - Components: `src/components/*`

---

## Environment Variables (backend/.env)

- `OPENAI_API_KEY` – required (embeddings + optionally chat)
- `ANTHROPIC_API_KEY` – optional (if the agent model is Anthropic)
- `TOKENCRUSH_API_KEY` – optional (bulletin chunk optimization)
- `HOST=0.0.0.0` – server host
- `PORT=8000` – server port
- `RELOAD=true` – dev mode live-reload

If you change providers/models, update `backend/agent/graph/agent.py` accordingly. The agent currently uses OpenAI's GPT model by default.

---

## Data and Vector Stores

- Course CSV location is resolved via `backend/databases/paths.py`. Default filename is set in `DatabaseCache.load_course_df`.
- Bulletin PDF defaults to `backend/databases/data/misc/Bulletin_2025-2026_PDF_with_cover_page_.pdf`. Parsed chunks are cached to `backend/databases/cache/bulletin_documents.pkl`.
- Chroma persist directories:
  - Courses: `backend/databases/data/course_chroma_db`
  - Bulletin: `backend/databases/data/bulletin_chroma_db`

Rebuild instructions are in the Quick Start section.

---

## Testing

Tests are located in `backend/tests/`:
- `unit_tests/` - Unit tests for agent tools, LLM manager, prompts, configuration
- `integration_tests/` - Integration tests for the agent graph
- `test_filter_speed.py`, `test_query_speed.py` - Performance benchmarks

Run tests:
```bash
cd backend
pytest -q                    # Run all tests
pytest tests/unit_tests -q   # Run unit tests only
pytest tests/integration_tests -q  # Run integration tests only
```

---

## Deployment

- For containerized deployments, consider a two-stage Dockerfile (backend + frontend build) and setting the required env vars in your platform.
- Ensure vector DBs are built and persisted on a writable volume or build them during image build.
- Make sure log directories (`backend/agent/logs/`) are writable in production.

---

## Troubleshooting

- Backend fails at startup with "Course database not found":
  - Run the course builder (see Quick Start step 2) and ensure the CSV path is correct.
- SSE stream terminates immediately:
  - Confirm the model credentials and that the agent can call tools without errors (check `backend/agent/logs/api.log`).
- CORS or fetch errors in frontend:
  - Verify `VITE_API_URL` and that backend listens on `http://localhost:8000`.
- High token usage on bulletin:
  - Provide `TOKENCRUSH_API_KEY` or set `use_tokencrush=False` in the builder if needed.
- Debugging tool execution:
  - Check `backend/agent/logs/tools.log` for detailed tool call logs with inputs and outputs.
  - Check `backend/agent/logs/agent.log` for streaming events and LLM interactions.

---

## Roadmap & Presentation Prep

- Improve test coverage; replace placeholder tests with focused unit/integration tests
- Add architecture diagram (agent + tools + vector stores + SSE)
- Capture a short demo script with 3–4 representative user prompts
- Add screenshots/gifs of the chat UI (light + dark)
- Add LICENSE and CONTRIBUTING
- Add pre-commit hooks (black/ruff/isort for Python; eslint/prettier for frontend)
- Optional: Docker Compose for one-command local run

---

## License

Add your preferred license (e.g., MIT) as `LICENSE` in the project root.


