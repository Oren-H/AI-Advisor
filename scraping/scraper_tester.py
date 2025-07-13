import asyncio
import pandas as pd
from scraping.columbia_course_scraper import ColumbiaCourseScraper
from datetime import datetime
import json

async def test_specific_department(url: str):
    """Test the scraper on a specific department URL."""
    print(f"Testing Columbia Course Scraper on: {url}")
    print("=" * 70)
    
    # Initialize scraper
    scraper = ColumbiaCourseScraper()
    
    try:
        # Setup the scraper
        await scraper.setup()
        print("✓ Browser setup completed")
        
        # Clear any existing courses
        scraper.courses = []
        
        # Test the specific department
        await scraper.scrape_department(url)
        
        # Display results
        if scraper.courses:
            print(f"\n✓ Successfully scraped {len(scraper.courses)} courses")
            
            # Separate courses with valid course codes from those with "N/A"
            valid_courses = []
            invalid_courses = []
            
            for course in scraper.courses:
                if course['course_code'] == "N/A":
                    invalid_courses.append(course)
                else:
                    valid_courses.append(course)
            
            print(f"  - Valid courses (with course codes): {len(valid_courses)}")
            print(f"  - Invalid courses (N/A course codes): {len(invalid_courses)}")
            
            # Display first few valid courses for preview
            if valid_courses:
                print("\nFirst 3 valid courses found:")
                print("-" * 70)
                for i, course in enumerate(valid_courses[:3]):
                    print(f"\nCourse {i+1}:")
                    print(f"  Code: {course['course_code']}")
                    print(f"  Title: {course['course_title']}")
                    print(f"  Department: {course['department']}")
                    print(f"  Section: {course['section']}")
                    print(f"  Times: {course['times']}")
                    print(f"  Location: {course['location']}")
                    print(f"  Instructor: {course['instructor']}")
                    print(f"  Credits: {course['credits']}")
                    print(f"  Enrollment: {course['enrollment']}")
                    print(f"  Description: {course['description'][:100]}..." if len(course['description']) > 100 else f"  Description: {course['description']}")
            
            # Save test results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save valid courses
            if valid_courses:
                csv_filename = f"test_results_valid_{timestamp}.csv"
                json_filename = f"test_results_valid_{timestamp}.json"
                
                # Save as CSV
                df_valid = pd.DataFrame(valid_courses)
                df_valid.to_csv(csv_filename, index=False)
                
                # Save as JSON for better readability
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(valid_courses, f, indent=2, ensure_ascii=False)
                
                print(f"\n✓ Valid courses saved to:")
                print(f"  - {csv_filename}")
                print(f"  - {json_filename}")
            
            # Save invalid courses
            if invalid_courses:
                csv_filename_invalid = f"test_results_invalid_{timestamp}.csv"
                json_filename_invalid = f"test_results_invalid_{timestamp}.json"
                
                # Save as CSV
                df_invalid = pd.DataFrame(invalid_courses)
                df_invalid.to_csv(csv_filename_invalid, index=False)
                
                # Save as JSON for better readability
                with open(json_filename_invalid, 'w', encoding='utf-8') as f:
                    json.dump(invalid_courses, f, indent=2, ensure_ascii=False)
                
                print(f"\n✓ Invalid courses saved to:")
                print(f"  - {csv_filename_invalid}")
                print(f"  - {json_filename_invalid}")
            
            # Display summary statistics
            print(f"\nSummary Statistics:")
            print(f"  Total courses scraped: {len(scraper.courses)}")
            print(f"  Valid courses: {len(valid_courses)}")
            print(f"  Invalid courses: {len(invalid_courses)}")
            
            # Count unique departments (from valid courses only)
            departments = set(course['department'] for course in valid_courses if course['department'] != 'N/A')
            print(f"  Unique departments (valid): {len(departments)}")
            if departments:
                print(f"  Departments: {', '.join(sorted(departments))}")
            
            # Count courses with descriptions (from valid courses only)
            with_desc = len([c for c in valid_courses if c['description'] and c['description'] != 'N/A'])
            print(f"  Valid courses with descriptions: {with_desc}")
            
            # Count courses with instructors (from valid courses only)
            with_instructor = len([c for c in valid_courses if c['instructor'] and c['instructor'] != 'N/A'])
            print(f"  Valid courses with instructors: {with_instructor}")
            
        else:
            print("\n✗ No courses found")
            print("This could be due to:")
            print("  - Invalid URL")
            print("  - Page structure changes")
            print("  - Network issues")
            print("  - No courses listed on this page")
            
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        print("Error details:")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        await scraper.close()
        print("\n✓ Browser closed")

async def test_get_department_links():
    """Test the department link extraction functionality."""
    print("\nTesting Department Link Extraction")
    print("=" * 70)
    
    scraper = ColumbiaCourseScraper()
    
    try:
        await scraper.setup()
        print("✓ Browser setup completed")
        
        # Test department link extraction
        links = await scraper.get_department_links()
        
        if links:
            print(f"✓ Found {len(links)} department links")
            print("\nFirst 5 department links:")
            for i, link in enumerate(links[:5]):
                print(f"  {i+1}. {link}")
            
            if len(links) > 5:
                print(f"  ... and {len(links) - 5} more")
                
            # Save links to file
            with open('department_links.txt', 'w') as f:
                for link in links:
                    f.write(f"{link}\n")
            print(f"\n✓ All department links saved to 'department_links.txt'")
            
        else:
            print("✗ No department links found")
            
    except Exception as e:
        print(f"✗ Error getting department links: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()

async def main():
    """Main test function."""
    print("Columbia Course Scraper Test Suite")
    print("=" * 70)
    
    # Test specific department URL
    test_url = input("\nEnter department URL to test (or press Enter for default): ").strip()
    
    if not test_url:
        # Default test URL - Computer Science department
        test_url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/computer-science/"
        print(f"Using default URL: {test_url}")
    
    await test_specific_department(test_url)
    
    # Ask if user wants to test department link extraction
    test_links = input("\nDo you want to test department link extraction? (y/n): ").strip().lower()
    if test_links in ['y', 'yes']:
        await test_get_department_links()
    
    print("\n" + "=" * 70)
    print("Testing completed!")

if __name__ == "__main__":
    asyncio.run(main())