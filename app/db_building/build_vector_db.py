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
    
    # Convert time string to minutes from midnight
    def parse_time(time_str):
        if not time_str or time_str == 'N/A' or time_str.strip() == '':
            return None
        try: # hour value * 12 + minute value (12 hour clock, do not include am/pm)
            hour = time_str.split(":")[0]
            minute = time_str.split(":")[1].lower().rstrip("apm")
            return int(hour) * 60 + int(minute)
        except (ValueError, TypeError):
            return None

    # Parse time_starting and time_ending (already in minutes from midnight)
    time_starting_minutes = parse_time(row.get("scheduled_time_start"))
    time_ending_minutes = parse_time(row.get("scheduled_time_end"))
    
    # Adds all numerical data as metadata for each document
    meta.update({
        "course_code" : row["course_code"],
        "course_title" : row["course_title"],
        "instructor" : row["instructor"],
        "scheduled_time_start" : time_starting_minutes,
        "scheduled_time_end" : time_ending_minutes,
        "call_number" : row["call_number"],
        "campus" : row["campus"],
        "class_id" : row["class_id"],
        "course_subtitle" : row["course_subtitle"],
        "department" : row["department"],
        "department_code" : row["department_code"],
        "link" : row["link"],
        "location" : row["location"],
        "method_of_instruction" : row["method_of_instruction"],
        "open_to" : row["open_to"],
        "points" : row["points"],
        "scheduled_days" : row["scheduled_days"],
        "section_key" : row["section_key"],
        "type" : row["type"],  
    })

    '''
      {
    "course_code":"ACCT B6001",
    "course_title":"Financial Accounting",
    "course_descr":null,
    "instructor":"Yao Liu",
    "scheduled_time_start":"10:50am",
    "scheduled_time_end":"12:20pm",
    "call_number":"15846", 
    "campus":null,
    "class_id":"B6001-20251-001",
    "course_subtitle":null,
    "department":"Accounting (ACCT)",
    "department_code":"ACCT", 
    "instructor_wikipedia_link":null,
    "link":"https:\/\/doc.sis.columbia.edu\/subj\/ACCT\/B6001-20251-001\/",
    "location":"420 Kravis Hall",
    "method_of_instruction":"In-Person",
    "open_to":[
      "Business"
    ],
    "points":"3",
    "prerequisites":[

    ],
    "scheduled_days":"TR",
    "section_key":"20251ACCT6001B001",
    "type":"LECTURE"
    '''
    
    # semantic information to be embedded
    # Handle missing or N/A values
    course_title = row.get('course_title', None)
    course_subtitle = row.get('course_subtitle', None)
    course_code = row.get('course_code', None)
    course_descr = row.get('course_descr', None)
    prerequisites = row.get('prerequisites', None)

    doc.page_content = f"""{course_title} ({course_code})
        Course Subtitle: {course_subtitle}
        Description: {course_descr}
        Prerequisites: {prerequisites}
    """
    
    # Final check to ensure page_content is not None or empty
    if not doc.page_content or doc.page_content.strip() == "":
        return None
        
    return doc

def build_vector_database(csv_file="data/2025-Spring.csv", persist_directory="./data/chroma_db"):
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
    
    print(f"Vector database built and saved to {persist_directory}")
    print(f"Number of documents: {len(docs)}")
    print(f"Number of vectors in Chroma: {vectordb._collection.count()}")
    
    return vectordb

if __name__ == "__main__":
    # Only run this when you need to rebuild the database
    build_vector_database() 