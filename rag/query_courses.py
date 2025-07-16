from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from database_utils import load_vector_database

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
            description="The department that offers the course. Computer Science courses use 'COMS' or 'CSEE', not 'CS'. Other examples: 'MATH', 'PHYS', 'RELI', 'ARAM'. Use exact department codes as stored in the database.",
            type="string",
        ),
        AttributeInfo(
            name="section", 
            description="A code representing which section of the course is being offered", 
            type="string"
        ),
        AttributeInfo(
            name="days_offered",
            description="The days of the week the course is offered (e.g. MWF, TR, etc.)",
            type="string",
        ),
        AttributeInfo(
            name="time_starting",
            description="The start time of the course (e.g. 10:00AM)",
            type="string",
        ),
        AttributeInfo(
            name="time_ending",
            description="The end time of the course (e.g. 11:20AM)",
            type="string",
        ),
        AttributeInfo(
            name="credits", 
            description="The number of credits the course is worth (numeric value like 3.0, 4.0)",
            type="float",
        ),
        AttributeInfo(
            name="enrolled",
            description="The number of students enrolled in the course (e.g. 12/48)",
            type="float",
        ),
        AttributeInfo(
            name="max_enrollment",
            description="The maximum number of students that can be enrolled in the course (e.g. 48)",
            type="float",
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
    
    document_content_description = """
        Course name, description, prerequisites, corequisites.

        ### Filter syntax
        • Single condition → eq("field", value)
        • Multiple conditions → and(condition1, condition2, …)
        • When you need to match a substring, use contain("field", "value")

        **Examples**
        - eq("dept", "COMS")
        - contain("times", "TTh")
        - and(eq("dept", "COMS"), lte("credits", 3.5))
        - and(eq("dept", "COMS"), contains("times", "TTh"), lte("credits", 3.5))
        """
    
    llm = ChatOpenAI(temperature=0, model="gpt-4")
    retriever = SelfQueryRetriever.from_llm(
        llm,
        vectordb,
        document_content_description,
        metadata_field_info,
        verbose=True,
    )
    
    return retriever

def query_courses(query, k=1):
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
        retriever.verbose = True
        
        print(f"Querying: {query}")
        results = retriever.invoke(query)
        
        # Limit results to k and show the correct count
        limited_results = results[:k]
        print(f"\nFound {len(limited_results)} relevant course{'s' if len(limited_results) != 1 else ''}:")
        for i, doc in enumerate(limited_results, 1):
            print(f"\n{i}. {doc.metadata['course_title']} ({doc.metadata['course_code']})")
            print(f"   Department: {doc.metadata['dept']}")
            print(f"   Credits: {doc.metadata['credits']}")
            print(f"   Instructor: {doc.metadata['instructor']}")
            print(f"   Times: {doc.metadata['time_starting']} - {doc.metadata['time_ending']}")
            print(f"   Days: {doc.metadata['days_offered']}")
            print(f"   Enrolled: {doc.metadata['enrolled']} / {doc.metadata['max_enrollment']}")
            print(f"   Currently Offered: {doc.metadata['offered']}")
            print(f"   Content: {doc.page_content[:200]}...")
        
        return results
        
    except Exception as e:
        print(f"Error querying courses: {e}")
        return []

if __name__ == "__main__":
    # Example queries
    queries = [
        "Show me computer science courses with 3 credits offered on a Tuesday",
    ]
    
    for query in queries:
        print("=" * 60)
        query_courses(query)
        print() 