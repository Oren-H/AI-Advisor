
import os

from langchain.chat_models import init_chat_model
from langchain.tools import tool

openai_api_key = os.getenv("OPENAI_API_KEY")
model = init_chat_model("gpt-4o-mini")







@tool 
def retrieve_major_context(major: str, k: int = 5) -> str:
    """Get the major requirements from the bulletin using deterministic page mapping."""

    try:
        # First, try to get pages from the deterministic mapping
        page_numbers = MAJOR_PAGE_MAPPINGS.get(major)
        print(f"Retrieving pages {page_numbers} for {major}")

        # Retrieve documents for the specified pages
        context_chunks = []
        cache_path = "graph/__pklcache__/bulletin_doc_cache.pkl"
        bulletin_file_path = "major_scraping/Bulletin_2025-2026_PDF_with_cover_page_.pdf"
        documents = load_documents_with_cache(bulletin_file_path, cache_path)
        for page_num in page_numbers:
            try:
                page_doc = documents[page_num-1]
                if page_doc:
                    context_chunks.append(
                        f"Page {page_num}:\n{page_doc.page_content}"
                    )
                for i in range(k):
                    adj_docs = [documents[page_num-1-i], documents[page_num-1+i]]
                    context_chunks.append(
                        f"Page {page_num-i}:\n{adj_docs[0].page_content}"
                        f"Page {page_num+i}:\n{adj_docs[1].page_content}"
                    )
            except Exception as e:
                print(f"Error retrieving page {page_num}: {e}")
                continue

        if not context_chunks:
            return f"No content found for '{major}' on specified pages."

        context = "\n\n---\n\n".join(context_chunks)

        print(f"Major context: {context}")

        print(f"Retrieved {len(context_chunks)} pages for {major}")

        return (
            f"Major requirements for '{major}':\n\n"
            f"{context}\n\n"
            f"Sources: Pages {sorted(page_numbers)}"
        )
    except Exception as e:
        print(f"Error in get_major_requirements: {e}")
        return "I'm sorry, I'm having trouble getting the major requirements. Please try again."

@tool 
def plan_major(state: CourseAdvisorState) -> str:
    """Plan a major course schedule."""
    # to be implemented 
    return "Plan a major course schedule."
