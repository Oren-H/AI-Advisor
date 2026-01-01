# Database Standardization Plan for graph_router copy.py

## Overview
Standardize all database handling in `graph_router copy.py` by creating a centralized `DatabaseManager` singleton class. This will eliminate confusion from inconsistent paths, variable names, duplicate code, and different embedding models.

## Problem Summary

### Critical Issues Found
1. **Variable naming inconsistency**: `bulletin_db` vs `bulletin_vector_db` vs `course_db`
2. **Duplicate code**: `MAJOR_PAGE_MAPPINGS` defined twice, `get_major_requirements()` duplicated
3. **Relative paths**: Fragile paths like `"major_scraping/chroma_db/"` that break based on execution context
4. **Different embedding models**: Course DB uses `text-embedding-3-small`, Bulletin DB uses default (ada-002)
5. **Global variables**: `bulletin_vector_db = None` initialized but never properly set
6. **No centralization**: Each function manually loads databases

## Solution: DatabaseManager Singleton

Create a centralized `DatabaseManager` class modeled after the existing `LLMManager` pattern:
- Single source of truth for all database access
- Absolute paths using `Path(__file__).parent.parent`
- Consistent embedding models across all databases
- Lazy loading with caching (load once, reuse)
- Thread-safe for concurrent requests
- Clear error messages when databases are missing

---

## Implementation Steps

### Step 1: Create DatabaseManager Module

**File**: `/Users/alt2005/ai_advisor/AI-Advisor/agent/db_manager.py` (NEW)

**Key Features**:
- Singleton pattern (one instance per application)
- Methods: `get_course_db()`, `get_bulletin_db()`, `get_bulletin_documents()`
- Absolute paths for all databases
- Standardized embedding model: `text-embedding-3-small` for both DBs
- Thread-safe lazy loading with double-check locking
- PDF document caching with modification time checks
- `clear_cache()` method for memory management
- `get_database_info()` for debugging

**Key Implementation Details**:
```python
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    # Standardized embedding models
    COURSE_EMBEDDING_MODEL = "text-embedding-3-small"
    BULLETIN_EMBEDDING_MODEL = "text-embedding-3-small"

    def __new__(cls):
        # Singleton pattern with thread safety
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        # Absolute paths
        self._project_root = Path(__file__).parent.parent
        self._course_db_path = self._project_root / "course_data" / "chroma_db"
        self._bulletin_db_path = self._project_root / "agent" / "major_scraping" / "chroma_db"
        self._bulletin_pdf_path = self._project_root / "agent" / "major_scraping" / "Bulletin_2025-2026_PDF_with_cover_page_.pdf"
        self._bulletin_cache_path = self._project_root / "agent" / "graph" / "__pklcache__" / "bulletin_doc_cache.pkl"

        # Lazy-loaded instances
        self._course_db = None
        self._bulletin_db = None
        self._bulletin_documents = None

        # Thread locks for lazy loading
        self._course_db_lock = threading.Lock()
        self._bulletin_db_lock = threading.Lock()
        self._bulletin_docs_lock = threading.Lock()

        self._initialized = True
```

**Critical Methods**:
- `get_course_db(force_reload=False)`: Load/return course ChromaDB
- `get_bulletin_db(force_reload=False)`: Load/return bulletin ChromaDB
- `get_bulletin_documents(force_reload=False)`: Load/return PDF pages with pickle caching
- `clear_cache()`: Clear all cached instances
- `get_database_info()`: Return dict with paths, existence, document counts

### Step 2: Create Database Configuration Module

**File**: `/Users/alt2005/ai_advisor/AI-Advisor/agent/db_config.py` (NEW)

**Purpose**: Centralize all database-related constants

**Contents**:
```python
# Major page mappings for deterministic lookup
MAJOR_PAGE_MAPPINGS = {
    "Computer Science": [166, 167, 168],
    # Add more majors as they are mapped
}

# Database settings (for future use)
DB_SETTINGS = {
    "course": {
        "embedding_model": "text-embedding-3-small",
    },
    "bulletin": {
        "embedding_model": "text-embedding-3-small",
        "chunk_size": 1000,
        "chunk_overlap": 200,
    }
}
```

### Step 3: Migrate graph_router copy.py

**File**: `/Users/alt2005/ai_advisor/AI-Advisor/agent/graph/graph_router copy.py` (MODIFY)

**Changes**:

#### 3.1: Add imports (top of file)
```python
from agent.db_manager import db_manager
from agent.db_config import MAJOR_PAGE_MAPPINGS
```

#### 3.2: Remove global variables (lines 78-79)
**REMOVE**:
```python
bulletin_vector_db = None
course_vector_db = None
```

#### 3.3: Remove duplicate MAJOR_PAGE_MAPPINGS
- **KEEP**: First definition (around line 161-163)
- **REMOVE**: Duplicate definition (around line 238-240)
- **REPLACE BOTH** with import from `db_config`

#### 3.4: Update search_courses tool (lines 106-127)
**Current issues**:
- Line 122-123: Missing quotes around dict keys
- No use of db_manager

**Fix**:
```python
@tool(args_schema=SearchCoursesInput)
def search_courses(query: str, limit: int = 20, unique_courses_flag: bool = True) -> Dict[str, Any]:
    """Vector search for courses based on natural language query."""
    try:
        filters = generate_filters_from_prompt(query)

        course_results = query_courses_with_filters(
            query,
            filters=filters,
            k=limit,
            unique_courses_only=unique_courses_flag
        )

        return {
            "courses": course_results,  # ✅ Fixed quotes
            "total_count": len(course_results)
        }
    except Exception as e:
        print(f"Error in search_courses: {e}")
        return {"courses": [], "total_count": 0}
```

#### 3.5: Fix lookup_course tool (lines 129-152)
**Current issues**:
- References undefined `state` variable
- Line 147: Syntax error
- Doesn't use db_manager

**Fix**: Simplify to direct course code lookup
```python
@tool(description="Lookup a course by course code")
def lookup_course(course_code: str) -> Dict[str, Any]:
    """Direct lookup of a specific course by its exact code."""
    try:
        results = query_courses_with_filters(
            course_code,
            filters={},
            k=1,
            unique_courses_only=True
        )

        if results:
            return {"found": True, "course": results[0]}
        else:
            return {"found": False, "course": None}
    except Exception as e:
        print(f"Error in lookup_course: {e}")
        return {"found": False, "course": None}
```

#### 3.6: Update get_major_requirements function
**Current**: Has duplicate at lines 242-283
**Fix**: Keep ONE version using db_manager

```python
def get_major_requirements(major: str, k: int = 5) -> str:
    """Get major requirements using deterministic page mapping."""
    try:
        page_numbers = MAJOR_PAGE_MAPPINGS.get(major)
        if not page_numbers:
            return f"No page mapping found for major '{major}'"

        print(f"Retrieving pages {page_numbers} for {major}")

        # NEW: Use db_manager
        documents = db_manager.get_bulletin_documents()

        context_chunks = []
        for page_num in page_numbers:
            try:
                page_doc = documents[page_num - 1]
                if page_doc:
                    context_chunks.append(f"Page {page_num}:\n{page_doc.page_content}")

                # Add adjacent pages for context
                for i in range(1, k + 1):
                    if page_num - i >= 1:
                        context_chunks.append(f"Page {page_num-i}:\n{documents[page_num-1-i].page_content}")
                    if page_num + i <= len(documents):
                        context_chunks.append(f"Page {page_num+i}:\n{documents[page_num-1+i].page_content}")
            except Exception as e:
                print(f"Error retrieving page {page_num}: {e}")
                continue

        if not context_chunks:
            return f"No content found for '{major}'"

        context = "\n\n---\n\n".join(context_chunks)
        return f"Major requirements for '{major}':\n\n{context}\n\nSources: Pages {sorted(page_numbers)}"
    except Exception as e:
        print(f"Error in get_major_requirements: {e}")
        return "Error retrieving major requirements"
```

**REMOVE**: Duplicate function at lines 242-283

#### 3.7: Remove incomplete major_search function (lines 207-236)
This function appears to be incomplete/experimental and conflicts with other implementations.

**REMOVE ENTIRELY**

### Step 4: Update Supporting Files

#### 4.1: Update query_courses_from_filter.py

**File**: `/Users/alt2005/ai_advisor/AI-Advisor/agent/db_querying/query_courses_from_filter.py`

**Change** (lines 32-34):
```python
# OLD:
script_dir = os.path.dirname(os.path.abspath(__file__))
chroma_db_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "course_data", "chroma_db")
vectordb = load_vector_database(chroma_db_path)

# NEW:
from agent.db_manager import db_manager
vectordb = db_manager.get_course_db()
```

#### 4.2: Update graph.py

**File**: `/Users/alt2005/ai_advisor/AI-Advisor/agent/graph/graph.py`

**Changes**:
- Line 84: Remove `bulletin_db = None`
- Add import: `from agent.db_manager import db_manager`
- Update `major_search()` function (lines 171-218) to use `db_manager.get_bulletin_db()` instead of manual loading
- Update `get_major_requirements()` (lines 225-271) to use `db_manager.get_bulletin_documents()`

### Step 5: Update Build Scripts

#### 5.1: Standardize bulletin database embedding model

**File**: `/Users/alt2005/ai_advisor/AI-Advisor/agent/major_scraping/build_bulletin_vector_db.py`

**Change** (around line 60):
```python
# OLD:
embeddings = OpenAIEmbeddings()  # Uses default ada-002

# NEW:
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")  # Match course DB
```

**⚠️ CRITICAL**: After this change, you MUST rebuild the bulletin database:
```bash
python agent/major_scraping/build_bulletin_vector_db.py
```

---

## Migration Checklist

### Phase 1: Create New Modules
- [ ] Create `agent/db_manager.py` with full DatabaseManager implementation
- [ ] Create `agent/db_config.py` with MAJOR_PAGE_MAPPINGS
- [ ] Test DatabaseManager can load both databases

### Phase 2: Update graph_router copy.py
- [ ] Add imports for db_manager and db_config
- [ ] Remove global variables (bulletin_vector_db, course_vector_db)
- [ ] Fix search_courses tool (add quotes to dict keys)
- [ ] Fix lookup_course tool (remove state references, fix syntax)
- [ ] Update get_major_requirements to use db_manager
- [ ] Remove duplicate MAJOR_PAGE_MAPPINGS
- [ ] Remove duplicate get_major_requirements function
- [ ] Remove incomplete major_search function (lines 207-236)

### Phase 3: Update Supporting Files
- [ ] Update query_courses_from_filter.py to use db_manager
- [ ] Update graph.py to use db_manager
- [ ] Update build_bulletin_vector_db.py to use text-embedding-3-small
- [ ] Rebuild bulletin database with new embedding model

### Phase 4: Testing
- [ ] Test course search works
- [ ] Test major requirements lookup works
- [ ] Test concurrent requests (thread safety)
- [ ] Test error handling when databases are missing
- [ ] Verify no import errors

---

## Critical Files to Modify

1. **`/Users/alt2005/ai_advisor/AI-Advisor/agent/db_manager.py`** (CREATE) - Core singleton manager
2. **`/Users/alt2005/ai_advisor/AI-Advisor/agent/db_config.py`** (CREATE) - Configuration constants
3. **`/Users/alt2005/ai_advisor/AI-Advisor/agent/graph/graph_router copy.py`** (MODIFY) - Main migration target
4. **`/Users/alt2005/ai_advisor/AI-Advisor/agent/db_querying/query_courses_from_filter.py`** (MODIFY) - Use db_manager
5. **`/Users/alt2005/ai_advisor/AI-Advisor/agent/graph/graph.py`** (MODIFY) - Use db_manager
6. **`/Users/alt2005/ai_advisor/AI-Advisor/agent/major_scraping/build_bulletin_vector_db.py`** (MODIFY) - Standardize embedding model

---

## Benefits After Standardization

✅ **Single source of truth** for all database access
✅ **No more path confusion** - absolute paths always work
✅ **Consistent embedding models** - same model for all databases
✅ **Thread-safe** - handles concurrent requests properly
✅ **Better error messages** - clear instructions when databases are missing
✅ **No code duplication** - one implementation, multiple uses
✅ **Easy to maintain** - update paths/config in one place
✅ **Memory efficient** - lazy loading with caching

---

## Edge Cases & Gotchas

1. **Embedding Model Change**: Changing bulletin DB embedding model requires rebuilding the database
2. **Thread Safety**: DatabaseManager uses double-check locking to prevent race conditions
3. **PDF Cache**: DatabaseManager checks file modification times to invalidate stale caches
4. **Missing Databases**: Clear FileNotFoundError with instructions on how to build
5. **Import Cycles**: Keep db_manager.py dependencies minimal (no agent.graph imports)

---

## Testing Strategy

After implementation:
```python
# Test script
from agent.db_manager import db_manager

# Test course DB
course_db = db_manager.get_course_db()
print(f"Course DB loaded: {course_db._collection.count()} docs")

# Test bulletin DB
bulletin_db = db_manager.get_bulletin_db()
print(f"Bulletin DB loaded: {bulletin_db._collection.count()} docs")

# Test bulletin documents
docs = db_manager.get_bulletin_documents()
print(f"Bulletin PDF: {len(docs)} pages")

# Test database info
print(db_manager.get_database_info())
```

Run the graph with a test query:
```python
python agent/graph/graph_router\ copy.py
```

Expected: No errors, consistent database access, proper responses.
