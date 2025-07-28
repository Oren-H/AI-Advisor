# AI Course Advisor

An intelligent course recommendation system for Columbia University students, powered by conversational AI and vector search.

## Overview

The AI Course Advisor is a comprehensive system that helps students find and select courses at Columbia University. It combines natural language processing, vector search, and conversational AI to provide personalized course recommendations based on student preferences, schedules, and academic goals.

## Features

- **Natural Language Queries**: Ask for courses in plain English
- **Intelligent Filtering**: Filter by department, time, days, credits, and course type
- **Conversational AI**: Interactive dialogue with memory of preferences
- **Vector Search**: Semantic search across course descriptions and metadata
- **Schedule Conflict Detection**: Avoid time conflicts between courses
- **User Profile Building**: Learn and remember student preferences over time

## Architecture

The system is built with a modular architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Data Layer    │
│   (React/TS)    │◄──►│   (Python)      │◄──►│   (Chroma DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   LangGraph     │
                       │   Workflow      │
                       └─────────────────┘
```

## Project Structure

```
AI-Advisor/
├── app/                          # Core application modules
│   ├── db_building/             # Vector database construction
│   ├── db_querying/             # Course search and filtering
│   └── graph/                   # Conversational AI workflow
├── data/                        # Course data and vector database
├── frontend/                    # React TypeScript frontend
├── scraping/                    # Course data scraping tools
├── tests/                       # Test suite
└── rag_env/                     # Python virtual environment
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Advisor
   ```

2. **Set up Python environment**
   ```bash
   python -m venv rag_env
   source rag_env/bin/activate  # On Windows: rag_env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp frontend/env.example frontend/.env
   # Add your OpenAI API key to .env
   ```

4. **Build the vector database**
   ```bash
   cd app/db_building
   python build_vector_db.py
   ```

5. **Start the backend**
   ```bash
   cd app/graph
   python graph_runner.py
   ```

6. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Usage Examples

### Course Search Queries

- "Show me computer science classes on Mondays and Wednesdays"
- "I need math classes in the morning"
- "Find literature courses with 3 credits"
- "What physics classes are available in the afternoon?"

### Advisory Queries

- "What should I take as a CS major?"
- "I'm interested in AI, what courses do you recommend?"
- "Help me plan my course schedule for next semester"

### Mixed Queries

- "I want to learn about machine learning and prefer afternoon classes"
- "As a freshman, what introductory courses should I take in the morning?"

## Core Modules

### Database Building (`app/db_building/`)
- Processes raw course data from CSV files
- Converts course information into vector embeddings
- Builds and persists Chroma vector database

### Database Querying (`app/db_querying/`)
- Generates structured filters from natural language
- Maps department names to Columbia University codes
- Executes semantic and metadata-based searches

### Conversational AI (`app/graph/`)
- LangGraph-based workflow for conversation management
- Intent classification and routing
- Memory management for user preferences
- Response generation with course recommendations

## Data Sources

- **Course Catalog**: Scraped from Columbia University's course directory
- **Course Descriptions**: Detailed information about each course
- **Schedule Information**: Times, days, locations, and instructors
- **Department Codes**: Official Columbia University department mappings

## API Endpoints

The system provides both programmatic and conversational interfaces:

### Conversational Interface
```python
from app.graph.graph_runner import run_course_advisor

response = run_course_advisor("I need computer science classes")
```

### Direct Database Queries
```python
from app.db_querying.generate_filters import generate_filters_from_prompt
from app.db_querying.query_courses_from_filter import query_courses

filters = generate_filters_from_prompt("computer science morning classes")
courses = query_courses(filters)
```

## Development

### Running Tests
```bash
cd tests
python -m pytest
```

### Adding New Features
1. Follow the modular architecture
2. Add tests for new functionality
3. Update relevant README files
4. Ensure compatibility with existing workflows

### Data Updates
To update course data:
1. Run the scraper: `python scraping/columbia_course_scraper.py`
2. Rebuild the vector database: `python app/db_building/build_vector_db.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Columbia University for course data
- OpenAI for language model APIs
- LangChain and LangGraph communities
- ChromaDB for vector database technology

## Support

For questions or issues, please open an issue on the GitHub repository or contact the development team. 