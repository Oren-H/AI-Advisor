from langchain_chroma import Chroma
import os

persist_dir = os.environ.get("CHROMA_DB_PATH", "/Users/alt2005/ai_advisor/AI-Advisor/data/chroma_db")

coll = Chroma(persist_directory=persist_dir, collection_name="course_code")
result = coll.get(where={"course_code": "COMS W4771"}, include=["metadatas","documents"])

print(result)