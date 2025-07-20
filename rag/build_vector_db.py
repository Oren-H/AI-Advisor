from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
import numpy as np

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def massage(doc):
    meta = doc.metadata
    
    # Parse the key-value format from CSVLoader
    content = doc.page_content.strip("'")
    if not content:
        # Skip documents with empty content
        return None
        
    row = {}
    for line in content.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            row[key.strip()] = value.strip()              
    
    # Convert credits to float, handling various formats
    credits_str = row.get("credits", "0")
    try:
        # Handle ranges like "2.00-6.00" by taking the first number
        if "-" in credits_str:
            credits = float(credits_str.split("-")[0])
        else:
            credits = float(credits_str)
    except (ValueError, TypeError):
        credits = 0.0
    
    # Convert offered to boolean
    offered_str = row.get("is_currently_offered", "False")
    offered = offered_str.lower() in ['true', '1', 'yes']
    
    # Adds all numerical data as metadata for each document
    meta.update({
        "course_title" : row["course_title"],
        "course_code" : row["course_code"],
        "dept"      : row["department"],
        "days_offered" : row["days_offered"],
        "time_starting" : row["time_starting"],
        "time_ending" : row["time_ending"],
        "section"   : row["section"],
        "credits"   : credits,  
        "enrolled" : row["enrolled"],
        "max_enrollment" : row["max_enrollment"],
        "instructor" : row["instructor"],
        "url" : row["url"],
        "offered" : offered, 
    })
    
    # semantic information to be embedded
    # Handle missing or N/A values
    title = row.get('course_title', 'Unknown Course')
    code = row.get('course_code', 'Unknown Code')
    description = row.get('description', 'No description available')
    prerequisites = row.get('prerequisites', 'No prerequisites listed')
    corequisites = row.get('corequisites', 'No corequisites listed')
    
    # Replace N/A values with meaningful text
    if description == 'N/A':
        description = 'No description available'
    if prerequisites == 'N/A':
        prerequisites = 'No prerequisites listed'
    if corequisites == 'N/A':
        corequisites = 'No corequisites listed'
    
    doc.page_content = f"""{title} ({code})
        Description: {description}
        Prerequisites: {prerequisites}
        Corequisites: {corequisites}"""
    
    # Final check to ensure page_content is not None or empty
    if not doc.page_content or doc.page_content.strip() == "":
        return None
        
    return doc

def build_vector_database(csv_file="Columbia Courses Final.csv", persist_directory="./chroma_db"):
    """
    Build and persist the vector database from CSV data.
    Only run this when your data changes.
    """
    print("Loading CSV data...")
    loader = CSVLoader(csv_file)
    docs = loader.load()
    
    print("Processing documents...")
    processed_docs = []
    for d in docs:
        processed_doc = massage(d)
        if processed_doc is not None:
            processed_docs.append(processed_doc)
    docs = processed_docs
    
    print("Creating embeddings and vector database...")
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vectordb = Chroma.from_documents(
        documents=docs, 
        embedding=emb,
        persist_directory=persist_directory
    )
    
    # Persist the database
    vectordb.persist()
    
    print(f"Vector database built and saved to {persist_directory}")
    print(f"Number of documents: {len(docs)}")
    print(f"Number of vectors in Chroma: {vectordb._collection.count()}")
    
    return vectordb

if __name__ == "__main__":
    # Only run this when you need to rebuild the database
    build_vector_database() 