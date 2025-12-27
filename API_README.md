# Course Advisor FastAPI

A FastAPI-based REST API that serves the Course Advisor AI system, providing course recommendations and advisory services through a conversational interface.

## Features

- 🤖 **AI-Powered Course Recommendations**: Uses LangGraph workflow for intelligent course suggestions
- 💬 **Conversational Interface**: Maintains conversation context and user profiles
- 🎯 **Intent Classification**: Automatically classifies user queries (specific, advisory, mixed)
- 🔍 **Smart Filtering**: Generates and applies course filters based on user preferences
- 📚 **Course Search**: Vector-based course search with metadata filtering
- 🧠 **Memory Management**: Maintains conversation history and user profiles
- 📊 **RESTful API**: Clean, documented API endpoints with automatic OpenAPI documentation

## Quick Start

### 1. Install Dependencies

```bash
# Install FastAPI dependencies
pip install -r requirements_api.txt

# Install main project dependencies
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Option 1: Use the startup script
python scripts/run_api.py

# Option 2: Use uvicorn directly
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## API Endpoints

### Health Check
```
GET /
```
Returns the health status of the API and graph readiness.

### Chat Interface
```
POST /chat
```
Main endpoint for course advisor interactions.

**Request Body:**
```json
{
  "message": "I'm looking for computer science courses for beginners",
  "conversation_id": "optional-existing-conversation-id",
  "user_profile": {
    "major": "Computer Science",
    "year": "1",
    "interests": ["programming", "algorithms"]
  }
}
```

**Response:**
```json
{
  "response": "Here are some great computer science courses for beginners...",
  "conversation_id": "generated-or-existing-id",
  "intent": "specific",
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
  },
  "error": null
}
```

### Conversation Management

#### List Conversations
```
GET /conversations
```
Returns a list of all active conversations.

#### Get Conversation Details
```
GET /conversations/{conversation_id}
```
Returns detailed information about a specific conversation including history.

#### Delete Conversation
```
DELETE /conversations/{conversation_id}
```
Deletes a specific conversation.

#### Clear All Conversations
```
DELETE /conversations
```
Clears all conversations (use with caution).

### User Profile Management

#### Get User Profile
```
GET /conversations/{conversation_id}/profile
```
Returns the user profile for a specific conversation.

#### Update User Profile
```
PUT /conversations/{conversation_id}/profile
```
Updates the user profile for a specific conversation.

## Usage Examples

### Python Client Example

```python
import requests

# Initialize conversation
response = requests.post("http://localhost:8000/chat", json={
    "message": "I need help choosing my first computer science course",
    "user_profile": {
        "major": "Computer Science",
        "year": "Freshman",
        "interests": ["programming", "problem solving"]
    }
})

conversation_id = response.json()["conversation_id"]
print(f"AI Response: {response.json()['response']}")

# Follow-up question
response = requests.post("http://localhost:8000/chat", json={
    "message": "What about courses that don't require programming experience?",
    "conversation_id": conversation_id
})

print(f"Follow-up Response: {response.json()['response']}")
```

### JavaScript/Node.js Example

```javascript
// Initial query
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: "I'm interested in data science courses",
    user_profile: {
      major: "Statistics",
      year: "Sophomore",
      interests: ["data analysis", "machine learning"]
    }
  })
});

const result = await response.json();
console.log('AI Response:', result.response);
console.log('Conversation ID:', result.conversation_id);

// Follow-up question
const followUpResponse = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: "Which of these courses have the best reviews?",
    conversation_id: result.conversation_id
  })
});

const followUpResult = await followUpResponse.json();
console.log('Follow-up Response:', followUpResult.response);
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/

# Start a conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to learn about artificial intelligence",
    "user_profile": {
      "major": "Computer Science",
      "year": "Junior"
    }
  }'

# Continue conversation (replace CONVERSATION_ID with actual ID)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What prerequisites do I need?",
    "conversation_id": "CONVERSATION_ID"
  }'

# List all conversations
curl http://localhost:8000/conversations
```

## Testing

Run the provided test script to verify the API functionality:

```bash
python tests/test_api.py
```

This will test all major endpoints and demonstrate conversation continuity.

## Configuration

### Environment Variables

- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `RELOAD`: Enable auto-reload for development (default: "false")

### Example Configuration

```bash
export HOST="127.0.0.1"
export PORT="8080"
export RELOAD="true"
python scripts/run_api.py
```

## Architecture

The API integrates with your existing LangGraph workflow:

1. **Request Processing**: Receives user queries and conversation context
2. **Graph Execution**: Runs the course advisor graph with the input state
3. **Memory Management**: Maintains conversation history and user profiles
4. **Response Generation**: Returns structured responses with course data

### Data Flow

```
User Request → FastAPI → LangGraph → Course Search → Response
     ↓              ↓         ↓           ↓           ↓
Conversation → Memory → Intent → Filters → Courses → JSON
   History      Update  Class.   Generate  Query    Response
```

## Production Considerations

1. **Database Storage**: Replace in-memory conversation storage with a proper database (PostgreSQL, MongoDB, etc.)
2. **Authentication**: Add user authentication and authorization
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **CORS Configuration**: Configure CORS properly for your frontend domain
5. **Logging**: Add structured logging for monitoring and debugging
6. **Error Handling**: Implement comprehensive error handling and validation
7. **Caching**: Add caching for frequently accessed data
8. **Load Balancing**: Use a load balancer for high availability

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and the Python path includes the project root
2. **Graph Initialization**: Check that the course advisor graph can be created successfully
3. **Database Connection**: Verify that any external databases (vector DB, etc.) are accessible
4. **Memory Issues**: Monitor memory usage, especially with large conversation histories

### Debug Mode

Enable debug mode for detailed logging:

```bash
export LOG_LEVEL="debug"
python scripts/run_api.py
```

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new endpoints
3. Update documentation for any API changes
4. Ensure all dependencies are properly specified

## License

This project follows the same license as the main Course Advisor project. 