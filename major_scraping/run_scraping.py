import asyncio
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import re
from urllib.parse import urljoin
import time
import requests
import json
import os

class ColumbiaMajorScraper:
    def __init__(self):
        self.base_url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/"

    async def setup(self):
        """Initialize Playwright browser for dynamic content scraping."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        # Set longer timeout for navigation
        self.page.set_default_timeout(60000)  # 60 seconds
    
    async def get_department_links(self) -> List[str]:
        """Extract all department links from the main page."""
        try:
            await self.page.goto(self.base_url)
            # Wait for any link to appear
            await self.page.wait_for_selector('a')
            
            # Get all department links
            department_links = await self.page.query_selector_all('a')
            links = []
            for link in department_links:
                href = await link.get_attribute('href')
                if href and '/departments-instruction/' in href and href != self.base_url:
                    # Convert relative URL to absolute URL
                    absolute_url = urljoin("https://bulletin.columbia.edu", href)
                    if absolute_url not in links:  # Avoid duplicates
                        links.append(absolute_url)
            
            print(f"Found {len(links)} unique department links")
            return links
            
        except Exception as e:
            print(f"Error getting department links: {e}")
            return []

    def get_html_content(self, url: str) -> str:
        """
        Get raw HTML content from a URL using the method from one_major.py.
        
        Args:
            url: The URL to scrape
            
        Returns:
            str: Raw HTML content
        """
        try:
            # Get the webpage content
            response = requests.get(url)
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            print(f"Error getting HTML from {url}: {e}")
            return ""

    def extract_department_name(self, url: str) -> str:
        """Extract department name from URL."""
        # Extract the last part of the URL path
        path_parts = url.rstrip('/').split('/')
        department = path_parts[-1] if path_parts else 'unknown'
        return department

    async def scrape_department_html(self, department_url: str) -> Dict:
        """Scrape HTML content for a single department's requirements and overview sections."""
        department_name = self.extract_department_name(department_url)
        print(f"Scraping department: {department_name}")
        
        # Create URLs for different sections (same format as one_major.py)
        requirements_url = f"{department_url}#requirementstext"
        overview_url = f"{department_url}#text"
        
        # Get HTML content for both sections
        requirements_html = self.get_html_content(requirements_url)
        overview_html = self.get_html_content(overview_url)
        
        # Return the data
        department_data = {
            'department_name': department_name,
            'department_url': department_url,
            'requirements_html': requirements_html,
            'overview_html': overview_html,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return department_data

    async def scrape_all_departments(self) -> List[Dict]:
        """Scrape all departments and return the HTML content."""
        await self.setup()
        
        try:
            # Get all department links
            department_links = await self.get_department_links()
            
            if not department_links:
                print("No department links found!")
                return []
            
            # Scrape each department
            all_data = []
            for i, link in enumerate(department_links, 1):
                print(f"Processing department {i}/{len(department_links)}: {link}")
                
                try:
                    department_data = await self.scrape_department_html(link)
                    all_data.append(department_data)
                    
                    # Add a small delay to be respectful to the server
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"Error scraping department {link}: {e}")
                    continue
            
            return all_data
            
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up Playwright resources."""
        if hasattr(self, 'context'):
            await self.context.close()
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    def save_data(self, data: List[Dict], output_file: str = 'columbia_majors_html.json'):
        """Save scraped HTML data to JSON file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"HTML data saved to {output_file}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def save_individual_files(self, data: List[Dict], output_dir: str = 'columbia_majors_html'):
        """Save each department's HTML content to individual files."""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            for dept in data:
                dept_name = dept['department_name']
                
                # Save requirements HTML
                if dept['requirements_html']:
                    req_filename = f"{output_dir}/{dept_name}_requirements.html"
                    with open(req_filename, 'w', encoding='utf-8') as f:
                        f.write(dept['requirements_html'])
                    print(f"Saved requirements HTML: {req_filename}")
                
                # Save overview HTML
                if dept['overview_html']:
                    ov_filename = f"{output_dir}/{dept_name}_overview.html"
                    with open(ov_filename, 'w', encoding='utf-8') as f:
                        f.write(dept['overview_html'])
                    print(f"Saved overview HTML: {ov_filename}")
            
            print(f"All HTML files saved to {output_dir}/")
            
        except Exception as e:
            print(f"Error saving individual files: {e}")

async def main():
    """Main function to run the scraper."""
    scraper = ColumbiaMajorScraper()
    
    print("Starting Columbia Major Scraper...")
    data = await scraper.scrape_all_departments()
    
    if data:
        print(f"Successfully scraped {len(data)} departments")
        
        # Save data in JSON format
        scraper.save_data(data, 'columbia_majors_html.json')
        
        # Save individual HTML files
        scraper.save_individual_files(data, 'columbia_majors_html')
        
        # Print summary
        print(f"Total departments processed: {len(data)}")
        
    else:
        print("No data was scraped.")

if __name__ == "__main__":
    asyncio.run(main())
        