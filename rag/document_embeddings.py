from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS        # swap with pgvector, Qdrant, etc.
import ast
from dotenv import load_dotenv
import os
import numpy as np

# Load environment variables from .env file
load_dotenv(dotenv_path="/Users/orenhartstein/AI-Advisor/.env")

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



#Sanity check. Remove later. 
print(f"Number of documents: {len(docs)}")
print(f"Number of vectors in FAISS: {vectordb.index.ntotal}")

# Get the embedding for the first document
embedding = emb.embed_query(docs[0].page_content)
print("Sample embedding:", embedding[:10])  # Print first 10 values

results = vectordb.similarity_search("machine learning", k=3)
for i, doc in enumerate(results):
    print(f"Result {i+1}: {doc.page_content[:100]}...")  # Print first 100 chars

embedding = emb.embed_query(docs[0].page_content)
print("Contains NaN:", np.isnan(embedding).any())
print("Contains Inf:", np.isinf(embedding).any())

print(docs[0].metadata)
