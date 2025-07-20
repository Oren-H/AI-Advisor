# Columbia Courses Vector Database

This directory contains a modular system for building and querying a vector database of Columbia University courses.

## Files Overview

- **`build_vector_db.py`** - Script to build the vector database from CSV data (run once)
- **`query_courses.py`** - Script to query the existing vector database
- **`database_utils.py`** - Utility functions for database management
- **`document_embeddings.py`** - Main interface that automatically handles building or querying

## Quick Start

### First Time Setup (Build Database)

```bash
# Build the vector database from your CSV file
python build_vector_db.py
```

This will:
- Load your CSV data
- Process and embed all course documents
- Save the vector database to `./chroma_db/`
- Only needs to be run when your data changes

### Query Courses

```bash
# Query the existing database
python query_courses.py
```

Or use the main interface:

```bash
# Automatically detects if database exists and builds/queries accordingly
python document_embeddings.py
```

### Check Database Status

```bash
# Check if database exists and get info
python database_utils.py
```

## Usage Examples

### Building the Database

```python
from build_vector_db import build_vector_database

# Build with default settings
build_vector_database()

# Or specify custom file and location
build_vector_database(
    csv_file="your_courses.csv",
    persist_directory="./my_custom_db"
)
```

### Querying Courses

```python
from query_courses import query_courses

# Simple query
results = query_courses("I want a Calculus course in the math department")

# Query with custom number of results
results = query_courses("Show me computer science courses", k=10)
```

### Database Utilities

```python
from database_utils import database_exists, get_database_info

# Check if database exists
if database_exists():
    print("Database is ready for querying!")

# Get detailed database info
info = get_database_info()
print(f"Database has {info['document_count']} documents")
```

## Workflow

1. **Initial Setup**: Run `build_vector_db.py` once to create the database
2. **Daily Usage**: Use `query_courses.py` or `document_embeddings.py` for queries
3. **Data Updates**: When your CSV data changes, run `build_vector_db.py` again

## Benefits of This Structure

- ✅ **No repeated vectorization** - Database is built once and reused
- ✅ **Fast queries** - No need to regenerate embeddings for each query
- ✅ **Modular design** - Separate concerns for building vs. querying
- ✅ **Easy maintenance** - Clear separation of database creation and usage
- ✅ **Automatic detection** - Main script automatically handles database existence

## File Structure

```
rag/
├── build_vector_db.py      # Database creation
├── query_courses.py        # Database querying
├── database_utils.py       # Utility functions
├── document_embeddings.py  # Main interface
├── chroma_db/             # Persistent database (created after first build)
└── README.md              # This file
```

## Troubleshooting

### Database Not Found Error
If you get a "Database not found" error:
1. Make sure you've run `build_vector_db.py` first
2. Check that the `chroma_db/` directory exists
3. Verify your CSV file path is correct

### Rebuilding the Database
To rebuild the database (e.g., after data changes):
1. Delete the `chroma_db/` directory: `rm -rf chroma_db/`
2. Run `build_vector_db.py` again

### Memory Issues
If you encounter memory issues with large datasets:
- Consider processing the CSV in chunks
- Use a smaller embedding model
- Increase your system's available memory 