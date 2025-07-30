# Frontend Integration Guide

This guide explains how to run the complete AI Advisor application with both the FastAPI backend and React frontend.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP Requests    ┌─────────────────┐
│   React Frontend │ ◄─────────────────► │  FastAPI Backend │
│   (Port 5173)   │                     │   (Port 8000)   │
└─────────────────┘                     └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │  LangGraph AI   │
                                    │   Workflow      │
                                    └─────────────────┘
```

## 🚀 Quick Start (Recommended)

### Option 1: Use the Development Script

The easiest way to start both servers:

```bash
# Make sure you're in the project root
./start_dev.sh
```

This script will:
- ✅ Check for required dependencies
- ✅ Install frontend dependencies if needed
- ✅ Start the FastAPI backend
- ✅ Start the React frontend
- ✅ Open both servers in your browser

### Option 2: Manual Startup

If you prefer to start servers manually:

#### 1. Start the Backend

```bash
# Install backend dependencies
pip install -r requirements_api.txt
pip install -r requirements.txt

# Start the FastAPI server
python scripts/run_api.py
```

The backend will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs

#### 2. Start the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:5173

## 🔧 Configuration

### Environment Variables

#### Frontend (.env file in frontend directory)

```bash
# API endpoint (default: http://localhost:8000)
VITE_API_URL=http://localhost:8000
```

#### Backend (environment variables)

```bash
# Server configuration
export HOST="0.0.0.0"
export PORT="8000"
export RELOAD="true"
```

### CORS Configuration

The FastAPI backend is configured to allow requests from the frontend. If you change the frontend port, update the CORS settings in `app/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📱 Using the Application

### 1. Open the Frontend

Navigate to http://localhost:5173 in your browser.

### 2. Start a Conversation

Type a message like:
- "I'm looking for computer science courses for beginners"
- "What courses are available in the spring semester?"
- "I need help choosing my major"

### 3. Follow-up Questions

The application maintains conversation context, so you can ask follow-up questions like:
- "What prerequisites do I need?"
- "Which of these courses have the best reviews?"
- "Tell me more about the first course"

### 4. View Course Results

When the AI finds relevant courses, they will be displayed in the chat interface with details like:
- Course code and title
- Description
- Credits
- Prerequisites

## 🔍 API Integration Details

### Frontend-Backend Communication

The frontend communicates with the backend through these endpoints:

#### Chat Endpoint
```typescript
POST /chat
{
  "message": "User query",
  "conversation_id": "optional-existing-id",
  "user_profile": {
    "major": "Computer Science",
    "year": "Freshman"
  }
}
```

#### Response Format
```typescript
{
  "response": "AI response text",
  "conversation_id": "unique-conversation-id",
  "intent": "specific|advisory|mixed",
  "course_results": [
    {
      "course_code": "COMS 1004",
      "title": "Introduction to Computer Science",
      "description": "...",
      "credits": 3
    }
  ],
  "filters": {
    "department": "COMS",
    "level": "introductory"
  }
}
```

### Conversation Management

The frontend automatically:
- ✅ Maintains conversation history in localStorage
- ✅ Sends conversation IDs for continuity
- ✅ Updates user profiles based on interactions
- ✅ Handles errors gracefully

## 🧪 Testing

### Test the API

```bash
# Test the backend API
python tests/test_api.py
```

### Test the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Run tests (if configured)
npm test

# Build for production
npm run build
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Make sure you're running from the project root:
```bash
cd /path/to/AI-Advisor
python scripts/run_api.py
```

#### 2. Frontend Can't Connect to Backend

**Error**: `Failed to fetch` or CORS errors

**Solutions**:
- Check that the backend is running on port 8000
- Verify the `VITE_API_URL` environment variable
- Check browser console for CORS errors

#### 3. Import Errors

**Error**: `Cannot resolve module` in frontend

**Solution**: Reinstall frontend dependencies:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 4. Port Already in Use

**Error**: `Address already in use`

**Solutions**:
- Kill existing processes: `lsof -ti:8000 | xargs kill -9`
- Change ports in configuration
- Use different ports for development

### Debug Mode

Enable debug logging:

```bash
# Backend debug
export LOG_LEVEL="debug"
python scripts/run_api.py

# Frontend debug (check browser console)
# Open browser dev tools and look for console logs
```

## 📊 Monitoring

### Backend Health Check

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "graph_ready": true
}
```

### Frontend Status

Check the browser console for:
- API connection status
- Conversation IDs
- Course results
- Error messages

## 🚀 Production Deployment

### Backend Deployment

1. **Build the application**:
   ```bash
   pip install -r requirements_api.txt
   pip install -r requirements.txt
   ```

2. **Use a production server**:
   ```bash
   gunicorn app.api:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Set up reverse proxy** (nginx/Apache)

### Frontend Deployment

1. **Build for production**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Serve static files**:
   ```bash
   npm install -g serve
   serve -s dist -l 3000
   ```

3. **Deploy to CDN** (Vercel, Netlify, etc.)

## 🔄 Development Workflow

1. **Start development environment**: `./start_dev.sh`
2. **Make changes** to frontend or backend code
3. **Auto-reload** will restart servers automatically
4. **Test changes** in the browser
5. **Commit changes** to version control

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## 🤝 Contributing

1. Follow the existing code structure
2. Test both frontend and backend changes
3. Update documentation for API changes
4. Ensure proper error handling
5. Add tests for new features 