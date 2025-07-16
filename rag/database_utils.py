import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def database_exists(persist_directory="./chroma_db"):
    """
    Check if the vector database exists on disk.
    
    Args:
        persist_directory (str): Path to the database directory
    
    Returns:
        bool: True if database exists, False otherwise
    """
    return os.path.exists(persist_directory)

def load_vector_database(persist_directory="./chroma_db"):
    """
    Load the existing vector database from disk.
    
    Args:
        persist_directory (str): Path to the database directory
    
    Returns:
        Chroma: The loaded vector database
        
    Raises:
        FileNotFoundError: If the database doesn't exist
    """
    if not database_exists(persist_directory):
        raise FileNotFoundError(
            f"Vector database not found at {persist_directory}. "
            "Please run build_vector_db.py first to create the database."
        )
    
    print(f"Loading vector database from {persist_directory}...")
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vectordb = Chroma(
        persist_directory=persist_directory,
        embedding_function=emb
    )
    
    print(f"Loaded database with {vectordb._collection.count()} documents")
    return vectordb

def get_database_info(persist_directory="./chroma_db"):
    """
    Get information about the existing vector database.
    
    Args:
        persist_directory (str): Path to the database directory
    
    Returns:
        dict: Database information including document count and size
    """
    if not database_exists(persist_directory):
        return {"exists": False, "error": "Database not found"}
    
    try:
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        vectordb = Chroma(
            persist_directory=persist_directory,
            embedding_function=emb
        )
        
        doc_count = vectordb._collection.count()
        
        # Calculate directory size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(persist_directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        return {
            "exists": True,
            "document_count": doc_count,
            "directory_size_mb": round(total_size / (1024 * 1024), 2),
            "persist_directory": persist_directory
        }
        
    except Exception as e:
        return {"exists": False, "error": str(e)}

def print_database_status():
    """
    Print the current status of the vector database.
    """
    info = get_database_info()
    
    if info["exists"]:
        print("✅ Vector database found!")
        print(f"   Documents: {info['document_count']}")
        print(f"   Size: {info['directory_size_mb']} MB")
        print(f"   Location: {info['persist_directory']}")
    else:
        print("❌ Vector database not found!")
        print(f"   Error: {info.get('error', 'Unknown error')}")
        print("   To create the database, run: python build_vector_db.py")

if __name__ == "__main__":
    print_database_status() 