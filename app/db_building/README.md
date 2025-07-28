# Database Building Module

This module handles the construction and setup of the vector database for course data.

## Purpose

The `db_building` module is responsible for:
- Processing raw course data from CSV files
- Converting course information into vector embeddings
- Building and persisting a Chroma vector database for semantic search

## Files

### `build_vector_db.py`
Main script for building the vector database from course CSV data.

**Key Functions:**
- `massage(doc)`: Processes and cleans individual course documents
- `build_vector_database()`: Main function that builds the vector database
- Handles time parsing, credit conversion, and metadata extraction

**Features:**
- Converts time strings to minutes from midnight for easier filtering
- Handles credit ranges (e.g., "2.00-6.00" → 2.0)
- Extracts comprehensive metadata for each course
- Uses OpenAI embeddings for vector search

### `database_utils.py`
Utility functions for database operations and data processing.

**Key Functions:**
- Database connection and management utilities
- Data validation and cleaning functions
- Helper functions for database queries

## Usage

```python
from build_vector_db import build_vector_database

# Build vector database from CSV file
build_vector_database(
    csv_file="2025-Spring.csv",
    persist_directory="./chroma_db"
)
```

## Dependencies

- `langchain_community.document_loaders.CSVLoader`
- `langchain_openai.OpenAIEmbeddings`
- `langchain_chroma.Chroma`
- `dotenv` for environment variable management

## Environment Variables

- `OPENAI_API_KEY`: Required for generating embeddings 