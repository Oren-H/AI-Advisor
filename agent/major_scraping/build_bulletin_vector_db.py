import os
import pickle
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_community.cache import InMemoryCache

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

def load_documents_with_cache(file_path, cache_path=None):
    """Load PDF documents with caching to avoid re-parsing."""
    if cache_path is None:
        cache_path = file_path.replace('.pdf', '_documents_cache.pkl') # should i delete this?  

    # Check if cache exists and is newer than the PDF
    if os.path.exists(cache_path):
        pdf_mtime = os.path.getmtime(file_path)
        cache_mtime = os.path.getmtime(cache_path)

        if cache_mtime > pdf_mtime:
            print(f"Loading cached documents from {cache_path}")
            with open(cache_path, 'rb') as f:
                documents = pickle.load(f)
            print(f"✓ Loaded {len(documents)} documents from cache")
            return documents

    # Cache miss or outdated - parse PDF
    print(f"Parsing PDF: {file_path}")
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # Save to cache
    print(f"Saving parsed documents to cache: {cache_path}")
    with open(cache_path, 'wb') as f:
        pickle.dump(documents, f)
    print(f"✓ Cached {len(documents)} documents")

    return documents

def create_chroma_db(file_path="major_scraping/Bulletin_2025-2026_PDF_with_cover_page_.pdf", persist_directory="major_scraping/chroma_db/", cache_path="app/graph/__pklcache__/bulletin_doc_cache.pkl"):
    """Create and persist Chroma vector database."""

    # Use cached document loading
    documents = load_documents_with_cache(file_path)
    print(f"Total characters: {sum(len(doc.page_content) for doc in documents)}")

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    texts = text_splitter.split_documents(documents)
    print("Total number of chunks:" + str(len(texts)))
    print(f"First chunk characters: {len(texts[0].page_content)}")

    embeddings = OpenAIEmbeddings()
    vector_db = Chroma.from_documents(texts, embeddings, persist_directory=persist_directory)

    print(f"Vector database built and saved to {persist_directory}")
    return vector_db



if __name__ == "__main__":
    db = create_chroma_db()