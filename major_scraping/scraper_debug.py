import asyncio
import json
import time
import traceback
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import scraping_functions as sf

class AllDepartmentsScraper:
    def __init__(self):
        self.base_url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_department_links(self) -> list:
        """Fetch and return all unique department URLs using requests."""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            anchors = soup.find_all('a')
            
            links = set()
            for a in anchors:
                href = a.get('href')
                if href and '/departments-instruction/' in href and href != self.base_url:
                    absolute = urljoin(self.base_url, href)
                    links.add(absolute)
            
            return sorted(links)
        except Exception as e:
            print(f"Error fetching department links: {e}")
            return []

    def cleanup(self):
        """Close session."""
        self.session.close()

def debug_scrape_department(url, department_name=None):
    """
    Debug version of scrape_department with detailed error tracking
    """
    print(f"Scraping department from: {url}")
    
    try:
        # Test the request first
        resp = requests.get(url)
        print(f"  Response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"  Error: Bad status code {resp.status_code}")
            return None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        print(f"  Page title: {soup.title.string if soup.title else 'No title'}")
        
        # Check for key elements
        course_block = soup.find(class_="courseblocktitle")
        print(f"  Course block found: {course_block is not None}")
        
        overview_container = soup.find(id="textcontainer")
        print(f"  Overview container found: {overview_container is not None}")
        
        requirements_container = soup.find(id="requirementstextcontainer")
        print(f"  Requirements container found: {requirements_container is not None}")
        
        # Now try the actual scraping with detailed error tracking
        data = sf.scrape_department(url, department_name)
        print(f"  Successfully scraped department: {data.get('department_name', 'Unknown')}")
        return data
        
    except Exception as e:
        print(f"  Error details:")
        print(f"    Exception type: {type(e).__name__}")
        print(f"    Exception message: {str(e)}")
        print(f"    Full traceback:")
        traceback.print_exc()
        return None

def main():
    scraper = AllDepartmentsScraper()
    print("Fetching department links...")
    dept_links = scraper.get_department_links()
    print(f"Found {len(dept_links)} department links.")

    # Test specific problematic URLs first
    test_urls = [
        "https://bulletin.columbia.edu/columbia-college/departments-instruction/public-health/",
        "https://bulletin.columbia.edu/columbia-college/departments-instruction/regional-studies/",
        "https://bulletin.columbia.edu/columbia-college/departments-instruction/religion/"
    ]
    
    print("\n=== Testing problematic URLs first ===")
    for url in test_urls:
        print(f"\n--- Testing: {url} ---")
        result = debug_scrape_department(url)
        if result:
            print(f"  ✓ Success!")
        else:
            print(f"  ✗ Failed!")
    
    # Continue with all URLs if you want
    print("\n=== Continue with all URLs? (y/n) ===")
    response = input().lower()
    if response != 'y':
        return

    all_departments = []
    for i, url in enumerate(dept_links, 1):
        print(f"\n[{i}/{len(dept_links)}] Scraping: {url}")
        result = debug_scrape_department(url)
        if result:
            result['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            all_departments.append(result)
        else:
            print(f"  Skipping due to error")

    scraper.cleanup()

    # Save collected data
    output_file = 'all_departments_debug.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_departments, f, indent=2, ensure_ascii=False)
    print(f"\nScraped data for {len(all_departments)} departments saved to {output_file}")

if __name__ == "__main__":
    main() 