from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS        # swap with pgvector, Qdrant, etc.
import ast
from dotenv import load_dotenv
import os
import sys

print(sys.executable)

# Load environment variables from .env file
load_dotenv(dotenv_path="/Users/orenhartstein/AI-Advisor/.env")
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

loader = CSVLoader("Columbia Courses Final.csv")               # one row → one Document
docs = loader.load()

def massage(doc):
    meta = doc.metadata
    
    # Parse the key-value format from CSVLoader
    content = doc.page_content.strip("'")
    row = {}
    for line in content.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            row[key.strip()] = value.strip()              
    
    #Adds all numerical data as metadata for each document
    meta.update({
        "course_title" : row["course_title"],
        "course_code" : row["course_code"],
        "dept"      : row["department"],
        "section"   : row["section"],
        "times"      : row["times"],      # e.g. "TTh"
        "credits"   : row["credits"],
        "enrollment" : row["enrollment"],
        "instructor" : row["instructor"],
        "url" : row["url"],
        "offered" : row["is_currently_offered"],
    })
    
    #semantic information to be embedded
    doc.page_content = f"""{row['course_title']} ({row['course_code']})
Description: {row['description']}
Prerequisites: {row['prerequisites']}
Corequisites: {row['corequisites']}"""
    return doc

docs = [massage(d) for d in docs]

emb = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = FAISS.from_documents(docs, emb)
