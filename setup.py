from setuptools import setup, find_packages

setup(
    name="ai-advisor",
    version="0.1.0",
    description="AI Course Advisor for Columbia University",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-openai",
        "langchain-chroma",
        "chromadb",
        "python-dotenv",
        "pydantic",
        "langgraph",
    ],
    python_requires=">=3.8",
) 