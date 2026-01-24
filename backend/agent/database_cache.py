"""
Centralized database caching for the application.
Databases are loaded once on app startup and kept in memory.
"""

import os
from typing import Optional

import pandas as pd
from backend.databases.build_bulletin_vector_db import load_documents_with_cache
from backend.databases.paths import (
    PROJECT_ROOT,
    course_csv_path,
    str_bulletin_cache_path,
    str_bulletin_db_dir,
    str_course_db_dir,
)
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class DatabaseCache:
    """Singleton cache for vector databases"""

    def __init__(self):
        self._course_db: Optional[Chroma] = None
        self._bulletin_db: Optional[Chroma] = None
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._course_df: Optional[pd.DataFrame] = None
        self._bulletin_documents: Optional[list] = None

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """Lazy-loaded embeddings instance (shared across both DBs)"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        return self._embeddings

    def load_course_db(self) -> Chroma:
        """Load course database from disk into memory"""
        if self._course_db is not None:
            return self._course_db

        print("Loading course vector database...")
        persist_dir = str_course_db_dir()

        if not os.path.exists(persist_dir):
            raise FileNotFoundError(
                f"Course database not found at {persist_dir}. "
            )

        self._course_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )

        doc_count = self._course_db._collection.count()
        print(f"Course DB loaded: {doc_count} documents")
        return self._course_db

    def load_bulletin_db(self) -> Optional[Chroma]:
        """Load bulletin database from disk into memory """
        if self._bulletin_db is not None:
            return self._bulletin_db

        print("Loading bulletin vector database...")
        persist_dir = str_bulletin_db_dir()
        print(persist_dir)

        if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
            print("Bulletin database not found - will be created on first use")
            return None

        self._bulletin_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )

        doc_count = self._bulletin_db._collection.count()
        print(f"Bulletin DB loaded: {doc_count} documents")

        return self._bulletin_db

    def load_bulletin_documents(self) -> list:
        """Load raw bulletin documents from PDF cache"""
        if self._bulletin_documents is not None:
            return self._bulletin_documents

        print("Loading bulletin documents from cache...")

        bulletin_file_path = str(PROJECT_ROOT / "databases" / "data" / "misc" / "Bulletin_2025-2026_PDF_with_cover_page_.pdf")
        cache_path = str_bulletin_cache_path()

        self._bulletin_documents = load_documents_with_cache(bulletin_file_path, cache_path)
        print(f"Loaded {len(self._bulletin_documents)} bulletin documents")
        return self._bulletin_documents
    
    def load_course_df(self, filename: str = "columbia-catalog-data/classes/2026-Spring.csv") -> pd.DataFrame:
        """Load course dataframe from disk into memory (lazy, cached)."""
        if self._course_df is not None:
            return self._course_df
        print("Loading course dataframe...")
        csv_path = course_csv_path(filename)
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"Course CSV not found at {csv_path}. "
            )
        self._course_df = pd.read_csv(csv_path)
        return self._course_df

    def get_course_db(self) -> Chroma:
        """Get cached course database"""
        if self._course_db is None:
            self._course_db = self.load_course_db()
        return self._course_db

    def get_course_df(self) -> pd.DataFrame:
        """Get cached course DataFrame"""
        if self._course_df is None:
            self._course_df = self.load_course_df()
        return self._course_df

    def get_bulletin_db(self) -> Optional[Chroma]:
        """Get cached bulletin database"""
        if self._bulletin_db is None:
            self._bulletin_db = self.load_bulletin_db()
        return self._bulletin_db

    def get_bulletin_documents(self) -> list:
        """Get cached bulletin documents"""
        if self._bulletin_documents is None:
            self._bulletin_documents = self.load_bulletin_documents()
        return self._bulletin_documents

    def close(self):
        """Cleanup on shutdown"""
        print("Closing database connections...")
        self._course_db = None
        self._bulletin_db = None
        self._course_df = None
        self._embeddings = None
        self._bulletin_documents = None
        print("Database cache cleared")

# Global singleton instance
db_cache = DatabaseCache()

if __name__ == "__main__":
    db_cache = DatabaseCache()
    
    db_cache.load_course_df()
    db_cache.load_course_db()
    db_cache.load_bulletin_documents()
    db_cache.load_bulletin_db()

    db_cache.close()
