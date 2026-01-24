"""
Test script to measure the performance of generate_filters_from_prompt
"""
import sys
import time
from pathlib import Path

# Add backend directory to path
tests_dir = Path(__file__).parent
backend_dir = tests_dir.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Import after setting up paths
from backend.agent.db_querying.generate_course_filters import generate_filters_from_prompt

# Test queries
test_queries = [
    "machine learning classes on Mondays",
    "programming C++ Python algorithms",
    "probability stochastic processes quantitative finance",
    "Find me a math or computer science class after 2pm",
    "intro to computer science",
]

def test_filter_generation_speed(num_runs: int = 3):
    """Test the speed of filter generation"""
    print(f"Testing generate_filters_from_prompt with {num_runs} runs per query\n")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)

        times = []
        for i in range(num_runs):
            start = time.time()
            filters = generate_filters_from_prompt(query)
            end = time.time()
            elapsed = end - start
            times.append(elapsed)

            print(f"  Run {i+1}: {elapsed:.3f}s")
            if i == 0:  # Show filters only on first run
                print(f"  Filters: {filters}")

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print("=" * 80)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test filter generation speed")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--query", type=str, help="Single query to test")

    args = parser.parse_args()

    if args.query:
        # Test single query
        print(f"Testing single query: {args.query}\n")
        print("=" * 80)

        times = []
        for i in range(args.runs):
            start = time.time()
            filters = generate_filters_from_prompt(args.query)
            end = time.time()
            elapsed = end - start
            times.append(elapsed)

            print(f"Run {i+1}: {elapsed:.3f}s")
            if i == 0:
                print(f"Filters: {filters}")

        avg_time = sum(times) / len(times)
        print(f"\nAverage: {avg_time:.3f}s")
    else:
        # Test all queries
        test_filter_generation_speed(args.runs)
