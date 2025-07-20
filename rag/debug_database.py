from database_utils import load_vector_database

def debug_database():
    """Debug the vector database to see what's stored."""
    try:
        vectordb = load_vector_database()
        
        # Get collection info
        collection = vectordb._collection
        print(f"Collection count: {collection.count()}")
        
        # Get all documents
        print("\nGetting all documents...")
        all_docs = collection.get()
        
        print(f"Total documents: {len(all_docs['documents'])}")
        print(f"Total metadatas: {len(all_docs['metadatas'])}")
        print(f"Total ids: {len(all_docs['ids'])}")
        
        # Show first few documents
        print("\nFirst 5 documents:")
        for i in range(min(5, len(all_docs['documents']))):
            print(f"\nDocument {i+1}:")
            print(f"  ID: {all_docs['ids'][i]}")
            print(f"  Content: {all_docs['documents'][i][:200]}...")
            print(f"  Metadata: {all_docs['metadatas'][i]}")
        
        # Check for COMS courses specifically
        print("\nLooking for COMS courses...")
        coms_count = 0
        for metadata in all_docs['metadatas']:
            if metadata and metadata.get('dept') == 'COMS':
                coms_count += 1
                if coms_count <= 3:  # Show first 3
                    print(f"  COMS course: {metadata.get('course_title', 'N/A')} ({metadata.get('course_code', 'N/A')})")
        
        print(f"Total COMS courses found: {coms_count}")
        
        # Check for MATH courses
        print("\nLooking for MATH courses...")
        math_count = 0
        for metadata in all_docs['metadatas']:
            if metadata and metadata.get('dept') == 'MATH':
                math_count += 1
                if math_count <= 3:  # Show first 3
                    print(f"  MATH course: {metadata.get('course_title', 'N/A')} ({metadata.get('course_code', 'N/A')})")
        
        print(f"Total MATH courses found: {math_count}")
        
        # Check unique departments
        print("\nUnique departments:")
        depts = set()
        for metadata in all_docs['metadatas']:
            if metadata and 'dept' in metadata:
                depts.add(metadata['dept'])
        
        for dept in sorted(depts):
            count = sum(1 for m in all_docs['metadatas'] if m and m.get('dept') == dept)
            print(f"  {dept}: {count} courses")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database() 