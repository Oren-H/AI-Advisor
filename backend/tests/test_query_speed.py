"""
Test script to measure the performance of query_courses_with_filters
"""
import sys
import time
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

# Add backend directory to path
tests_dir = Path(__file__).parent
backend_dir = tests_dir.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Import after setting up paths
from backend.agent.db_querying.query_courses_from_filter import query_courses_with_filters
from backend.agent.database_cache import db_cache

# Test cases with queries and filters
test_cases = [
    {
        "name": "Simple ML query",
        "query": "machine learning",
        "filters": {"department_code": {"$eq": "COMS"}},
        "k": 5,
    },
    {
        "name": "Math courses on Monday",
        "query": "calculus linear algebra",
        "filters": {
            "$and": [
                {"department_code": {"$eq": "MATH"}},
                {"scheduled_days": {"$eq": "M"}}
            ]
        },
        "k": 5,
    },
    {
        "name": "Stats courses after 2pm",
        "query": "probability statistics",
        "filters": {
            "$and": [
                {"department_code": {"$eq": "STAT"}},
                {"scheduled_time_start": {"$gte": 840}}  # 2pm in minutes
            ]
        },
        "k": 5,
    },
    {
        "name": "CS or EE courses (multi-dept)",
        "query": "algorithms data structures",
        "filters": {"department_code": {"$in": ["COMS", "ELEC"]}},
        "k": 10,
    },
    {
        "name": "No filters (semantic only)",
        "query": "artificial intelligence deep learning",
        "filters": None,
        "k": 5,
    },
]

def test_query_speed(num_runs: int = 3, suppress_output: bool = True):
    """Test the speed of course querying with filters"""

    # Warmup: Load database once
    print("Loading database...")
    try:
        db_cache.load_course_db()
        print("Database loaded successfully\n")
    except Exception as e:
        print(f"Error loading database: {e}")
        return

    print(f"Testing query_courses_with_filters with {num_runs} runs per test case\n")
    print("=" * 100)

    all_results = []

    for test_case in test_cases:
        name = test_case["name"]
        query = test_case["query"]
        filters = test_case["filters"]
        k = test_case["k"]

        print(f"\nTest: {name}")
        print(f"Query: {query}")
        print(f"Filters: {filters}")
        print(f"Requesting k={k} results")
        print("-" * 100)

        times = []
        result_counts = []

        for i in range(num_runs):
            # Suppress print statements from the function if requested
            if suppress_output:
                f = StringIO()
                with redirect_stdout(f):
                    start = time.time()
                    results = query_courses_with_filters(
                        query=query,
                        filters=filters,
                        k=k,
                        unique_courses_only=True,
                        reruns=3
                    )
                    end = time.time()
            else:
                start = time.time()
                results = query_courses_with_filters(
                    query=query,
                    filters=filters,
                    k=k,
                    unique_courses_only=True,
                    reruns=3
                )
                end = time.time()

            elapsed = end - start
            times.append(elapsed)
            result_counts.append(len(results))

            print(f"  Run {i+1}: {elapsed:.3f}s ({len(results)} results)")

            # Show sample results on first run
            if i == 0 and results:
                print(f"  Sample results:")
                for idx, course in enumerate(results[:3], 1):
                    code = course.get('course_code', 'N/A')
                    title = course.get('course_title', 'N/A')
                    score = course.get('similarity_score')
                    score_str = f" (score: {score:.4f})" if score else ""
                    print(f"    {idx}. {code}: {title}{score_str}")

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_results = sum(result_counts) / len(result_counts)

        test_result = {
            "name": name,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "avg_results": avg_results,
        }
        all_results.append(test_result)

        print(f"\n  Average time: {avg_time:.3f}s")
        print(f"  Min time: {min_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  Avg results returned: {avg_results:.1f}")
        print("=" * 100)

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"{'Test Name':<30} {'Avg Time':<12} {'Min Time':<12} {'Max Time':<12} {'Avg Results':<12}")
    print("-" * 100)
    for result in all_results:
        print(f"{result['name']:<30} {result['avg_time']:<12.3f} {result['min_time']:<12.3f} "
              f"{result['max_time']:<12.3f} {result['avg_results']:<12.1f}")

    overall_avg = sum(r['avg_time'] for r in all_results) / len(all_results)
    print("-" * 100)
    print(f"{'Overall Average':<30} {overall_avg:<12.3f}")
    print("=" * 100)

def test_single_query(query: str, filters: dict = None, k: int = 5, num_runs: int = 3):
    """Test a single query"""
    # Load database
    print("Loading database...")
    try:
        db_cache.load_course_db()
        print("Database loaded successfully\n")
    except Exception as e:
        print(f"Error loading database: {e}")
        return

    print(f"Testing single query with {num_runs} runs")
    print("=" * 100)
    print(f"Query: {query}")
    print(f"Filters: {filters}")
    print(f"k: {k}")
    print("-" * 100)

    times = []
    for i in range(num_runs):
        # Suppress output for timing
        f = StringIO()
        with redirect_stdout(f):
            start = time.time()
            results = query_courses_with_filters(
                query=query,
                filters=filters,
                k=k,
                unique_courses_only=True,
                reruns=3
            )
            end = time.time()

        elapsed = end - start
        times.append(elapsed)
        print(f"Run {i+1}: {elapsed:.3f}s ({len(results)} results)")

    avg_time = sum(times) / len(times)
    print(f"\nAverage time: {avg_time:.3f}s")

    # Show results
    if results:
        print(f"\nResults ({len(results)} courses):")
        for idx, course in enumerate(results, 1):
            code = course.get('course_code', 'N/A')
            title = course.get('course_title', 'N/A')
            score = course.get('similarity_score')
            score_str = f" (score: {score:.4f})" if score else ""
            print(f"  {idx}. {code}: {title}{score_str}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test course query speed")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per test case")
    parser.add_argument("--query", type=str, help="Single query to test")
    parser.add_argument("--filter", type=str, help="Filter as JSON string (e.g., '{\"department_code\": {\"$eq\": \"COMS\"}}')")
    parser.add_argument("--k", type=int, default=5, help="Number of results to retrieve")
    parser.add_argument("--verbose", action="store_true", help="Show query function output")

    args = parser.parse_args()

    if args.query:
        # Test single query
        filters = None
        if args.filter:
            import json
            try:
                filters = json.loads(args.filter)
            except json.JSONDecodeError as e:
                print(f"Error parsing filter JSON: {e}")
                sys.exit(1)

        test_single_query(args.query, filters, args.k, args.runs)
    else:
        # Test all cases
        test_query_speed(args.runs, suppress_output=not args.verbose)
