#!/usr/bin/env python3
"""
Test script for the Course Advisor FastAPI
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health check endpoint"""
    print("🏥 Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_chat():
    """Test the chat endpoint"""
    print("💬 Testing chat endpoint...")
    
    # Test data
    chat_data = {
        "message": "I'm looking for computer science courses for beginners",
        "user_profile": {
            "major": "Computer Science",
            "year": "Freshman",
            "interests": ["programming", "algorithms"]
        }
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result['response'][:200]}...")
        print(f"Intent: {result['intent']}")
        print(f"Conversation ID: {result['conversation_id']}")
        if result.get('course_results'):
            print(f"Found {len(result['course_results'])} courses")
        if result.get('filters'):
            print(f"Filters: {result['filters']}")
        
        return result['conversation_id']
    else:
        print(f"Error: {response.text}")
        return None
    print()

def test_conversation_continuity(conversation_id):
    """Test conversation continuity with follow-up questions"""
    if not conversation_id:
        print("❌ No conversation ID available for continuity test")
        return
    
    print(f"🔄 Testing conversation continuity with ID: {conversation_id}")
    
    # Follow-up question
    follow_up_data = {
        "message": "What about courses with prerequisites?",
        "conversation_id": conversation_id
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=follow_up_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Follow-up Response: {result['response'][:200]}...")
        print(f"Intent: {result['intent']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_conversations_list():
    """Test listing conversations"""
    print("📋 Testing conversations list...")
    response = requests.get(f"{BASE_URL}/conversations")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        conversations = response.json()
        print(f"Found {len(conversations)} conversations")
        for conv in conversations:
            print(f"  - {conv['conversation_id']}: {conv['message_count']} messages")
    else:
        print(f"Error: {response.text}")
    print()

def test_conversation_details(conversation_id):
    """Test getting conversation details"""
    if not conversation_id:
        print("❌ No conversation ID available for details test")
        return
    
    print(f"📄 Testing conversation details for ID: {conversation_id}")
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        details = response.json()
        print(f"Message count: {details['message_count']}")
        print(f"User profile: {details.get('user_profile', {})}")
        print(f"History length: {len(details.get('history', []))}")
    else:
        print(f"Error: {response.text}")
    print()

def main():
    """Run all tests"""
    print("🧪 Starting API tests...")
    print("=" * 50)
    
    # Test health check
    test_health()
    
    # Test chat
    conversation_id = test_chat()
    
    # Test conversation continuity
    test_conversation_continuity(conversation_id)
    
    # Test conversations list
    test_conversations_list()
    
    # Test conversation details
    test_conversation_details(conversation_id)
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    main() 