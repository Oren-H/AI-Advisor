"""
Simple Flask backend example for testing the AI Advisor frontend.
This is just for development/testing - use your actual RAG backend in production.
"""

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import time
import random

app = Flask(__name__)
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Mock chat endpoint that streams tokens like OpenAI's API."""
    data = request.get_json()
    message = data.get('message', '')
    
    # Mock response based on user input
    if 'machine learning' in message.lower() or 'computer science' in message.lower():
        response_text = "I found several machine learning courses in the Computer Science department:\n\n1. **COMS 4771** - Machine Learning (3 credits)\n2. **COMS 4772** - Advanced Machine Learning (3 credits)\n3. **COMS 4773** - Statistical Learning Theory (3 credits)\n\nThese courses cover topics like supervised learning, neural networks, and statistical methods."
    elif 'calculus' in message.lower():
        response_text = "For Calculus I, the typical prerequisites are:\n\n- High school algebra and trigonometry\n- Placement test or equivalent coursework\n- **MATH 1101** - Calculus I (3 credits)\n\nThis course covers limits, derivatives, and applications of differentiation."
    elif 'tuesday' in message.lower() or '3 pm' in message.lower():
        response_text = "Here are courses offered on Tuesdays after 3 PM:\n\n- **COMS 3157** - Advanced Programming (Tuesdays 4:10-6:40 PM)\n- **MATH 2010** - Linear Algebra (Tuesdays 3:10-5:40 PM)\n- **PHYS 1401** - Introduction to Mechanics (Tuesdays 4:10-6:40 PM)"
    elif 'psychology' in message.lower():
        response_text = "The Psychology department offers many courses:\n\n- **PSYC 1001** - Introduction to Psychology\n- **PSYC 1010** - Statistics and Research Methods\n- **PSYC 2001** - Cognitive Psychology\n- **PSYC 2002** - Social Psychology\n\nWould you like more specific information about any of these courses?"
    else:
        response_text = "I'm here to help you find Columbia University courses! You can ask me about:\n\n- Course availability and schedules\n- Prerequisites and requirements\n- Department-specific courses\n- Course descriptions and credits\n\nTry asking about specific courses, departments, or time slots."
    
    def generate():
        # Split response into tokens and stream them
        tokens = response_text.split(' ')
        for i, token in enumerate(tokens):
            # Add space between tokens (except first token)
            if i > 0:
                yield f"data: {json.dumps({'token': ' '})}\n\n"
            yield f"data: {json.dumps({'token': token})}\n\n"
            time.sleep(0.1)  # Simulate processing time
        
        yield "data: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'AI Advisor backend is running'})

if __name__ == '__main__':
    print("Starting AI Advisor backend server...")
    print("Frontend should be configured to connect to: http://localhost:5000")
    print("Make sure to set VITE_API_URL=http://localhost:5000 in your .env file")
    app.run(debug=True, port=5000) 