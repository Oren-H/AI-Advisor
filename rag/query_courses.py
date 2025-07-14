from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(dotenv_path="/Users/orenhartstein/AI-Advisor/.env")

def load_vector_database(persist_directory="./chroma_db"):
    """
    Load the existing vector database from disk.
    """
    if not os.path.exists(persist_directory):
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

def create_retriever(vectordb):
    """
    Create a SelfQueryRetriever for the vector database.
    """
    metadata_field_info = [
        AttributeInfo(
            name="course_title",
            description="The title of the college course",
            type="string",
        ),
        AttributeInfo(
            name="course_code",
            description="A code that includes the department and course number (e.g. CS 1101)",
            type="string",
        ),
        AttributeInfo(
            name="dept",
            description="The department that offers the course (e.g. CS, MATH, etc.). Use exact department codes like 'MATH', 'CS', 'PHYS'",
            type="string",
        ),
        AttributeInfo(
            name="section", 
            description="A code representing which section of the course is being offered", 
            type="string"
        ),
        AttributeInfo(
            name="times",
            description="The days and times the course is offered (e.g. Th 10:00-11:20)",
            type="string",
        ),
        AttributeInfo(
            name="credits",
            description="The number of credits the course is worth (numeric value like 3.0, 4.0)",
            type="float",
        ),
        AttributeInfo(
            name="enrollment",
            description="The number of students enrolled in the course (e.g. 12/48)",
            type="string",
        ),
        AttributeInfo(
            name="instructor",
            description="The name of the instructor teaching the course",
            type="string",
        ),
        AttributeInfo(
            name="url",
            description="The URL of the course",
            type="string",
        ),
        AttributeInfo(
            name="offered",
            description="Whether the course is currently being offered (True or False)",
            type="boolean",
        ),
    ]
    
    document_content_description = "Course name, description, and pre and corequisites. When constructing filters, use logical operators like 'and' and 'or' to combine multiple conditions. For example: and(eq('dept', 'MATH'), eq('credits', 3.0))"
    
    llm = ChatOpenAI(temperature=0)
    retriever = SelfQueryRetriever.from_llm(
        llm,
        vectordb,
        document_content_description,
        metadata_field_info,
    )
    
    return retriever

def query_courses(query, k=5):
    """
    Query the course database with a natural language query.
    
    Args:
        query (str): Natural language query about courses
        k (int): Number of results to return
    
    Returns:
        List of relevant course documents
    """
    try:
        vectordb = load_vector_database()
        retriever = create_retriever(vectordb)
        
        print(f"Querying: {query}")
        results = retriever.get_relevant_documents(query)
        
        print(f"\nFound {len(results)} relevant courses:")
        for i, doc in enumerate(results[:k], 1):
            print(f"\n{i}. {doc.metadata['course_title']} ({doc.metadata['course_code']})")
            print(f"   Department: {doc.metadata['dept']}")
            print(f"   Credits: {doc.metadata['credits']}")
            print(f"   Instructor: {doc.metadata['instructor']}")
            print(f"   Times: {doc.metadata['times']}")
            print(f"   Currently Offered: {doc.metadata['offered']}")
            print(f"   Content: {doc.page_content[:200]}...")
        
        return results
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

if __name__ == "__main__":
    # Example queries
    queries = [
        "I want a Calculus course in the math department",
        "Show me computer science courses with 3 credits",
        "Find courses taught by John Smith",
        "What machine learning courses are available?"
    ]
    
    for query in queries:
        print("=" * 60)
        query_courses(query)
        print() 