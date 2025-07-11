import asyncio
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import re
from urllib.parse import urljoin
import time

class ColumbiaCourseScraper:
    def __init__(self):
        self.base_url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/"
        self.courses = []

    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        # Set longer timeout for navigation
        self.page.set_default_timeout(60000)  # 60 seconds

    async def close(self):
        await self.browser.close()
        await self.playwright.stop()

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

    def parse_course_info(self, html: str, page_url: str) -> List[Dict]:
        """Parse course information from HTML content."""
        soup = BeautifulSoup(html, 'lxml')
        courses = []
        
        # Find all course blocks
        course_blocks = soup.find_all('div', class_='courseblock')
        
        for block in course_blocks:
            try:
                # Extract course title
                title_block = block.find('p', class_='courseblocktitle')
                if not title_block:
                    continue
                
                # Get the full title text
                full_title = title_block.get_text().strip()
                
                # Extract credits from title block
                credits = "N/A"
                credits_match = re.search(r'(\d+(?:\.\d+)?)\s*points?\.?', full_title)
                if credits_match:
                    credits = credits_match.group(1)
                
                # Extract description
                desc_block = block.find('p', class_='courseblockdesc')
                description = desc_block.get_text().strip() if desc_block else ""
                
                # Find the schedule table
                schedule_table = block.find('table', class_='scheduletbl')
                if schedule_table:
                    # Get all rows except header rows
                    rows = schedule_table.find_all('tr')[2:]  # Skip header rows
                    
                    for row in rows:
                        # Extract section information
                        cells = row.find_all('td', class_='unifyRow1')
                        if len(cells) >= 6:  # Ensure we have all required columns
                            # Get course code from the first cell
                            course_code = cells[0].get_text().strip()
                            department = course_code.split()[0] if course_code else "N/A"
                            
                            # Extract course title by removing course code and points
                            course_title = full_title
                            if course_code:
                                code_pattern = re.escape(course_code.split()[0]) + r'\s*[A-Z]*\s*' + re.escape(course_code.split()[1])
                                course_title = re.sub(rf'^{code_pattern}\s*', '', course_title)
                                # Remove trailing credit info like '3 points.', '3.0 points.', '3 pts.', etc.
                                course_title = re.sub(r'\s*\d+(?:\.\d+)?\s*points?\.?\s*$', '', course_title, flags=re.IGNORECASE)
                                course_title = re.sub(r'\s*\d+(?:\.\d+)?\s*$', '', course_title)  # Remove trailing numbers just in case
                                course_title = course_title.rstrip('.').strip()
                            
                            # Split times and location
                            times_location = cells[2].get_text().strip()
                            times = "N/A"
                            location = "N/A"
                            
                            # Try to split on newline or common location indicators
                            if times_location:
                                # Split on newline if present
                                parts = times_location.split('\n', 1)
                                if len(parts) == 2:
                                    times = parts[0].strip()
                                    location = parts[1].strip()
                                else:
                                    # If no newline, try to find location indicators
                                    location_match = re.search(r'(\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)*)$', times_location)
                                    if location_match:
                                        location = location_match.group(1).strip()
                                        times = times_location[:location_match.start()].strip()
                                    else:
                                        times = times_location
                            
                            section_info = {
                                'course_code': course_code,
                                'course_title': course_title,
                                'department': department,
                                'section': cells[1].get_text().strip(),
                                'times': times,
                                'location': location,
                                'instructor': cells[3].get_text().strip(),
                                'credits': cells[4].get_text().strip(),
                                'enrollment': cells[5].get_text().strip(),
                                'description': description,
                                'url': page_url
                            }
                            courses.append(section_info)
                else:
                    # If no schedule table, extract course code from title
                    course_code = "N/A"
                    department = "N/A"
                    course_title = full_title
                    
                    # Try to extract course code from the title
                    # Pattern: DEPT [W]#### Course Title. # points.
                    code_match = re.match(r'^([A-Z]{4})\s+([W]?\d{4})\s+(.+?)(?:\s*\d+(?:\.\d+)?\s*points?\.?)?$', full_title)
                    if code_match:
                        department = code_match.group(1)
                        course_number = code_match.group(2)
                        course_code = f"{department} {course_number}"
                        course_title = code_match.group(3).strip()
                        # Remove trailing credit info like '3 points.', '3.0 points.', etc.
                        course_title = re.sub(r'\s*\d+(?:\.\d+)?\s*points?\.?\s*$', '', course_title, flags=re.IGNORECASE)
                        course_title = re.sub(r'\s*\d+(?:\.\d+)?\s*$', '', course_title)
                        course_title = course_title.rstrip('.').strip()
                    else:
                        # Fallback: try a more flexible pattern
                        flexible_match = re.match(r'^([A-Z]{3,4})\s+([W]?\d{4})\s+(.+)', full_title)
                        if flexible_match:
                            department = flexible_match.group(1)
                            course_number = flexible_match.group(2)
                            course_code = f"{department} {course_number}"
                            remaining_title = flexible_match.group(3)
                            # Remove trailing credit info like '3 points.', '3.0 points.', etc.
                            course_title = re.sub(r'\s*\d+(?:\.\d+)?(?:-\d+)?\s*points?\.?\s*$', '', remaining_title, flags=re.IGNORECASE).strip()
                            course_title = re.sub(r'\s*\d+(?:\.\d+)?\s*$', '', course_title)
                            course_title = course_title.rstrip('.').strip()
                    
                    course_info = {
                        'course_code': course_code,
                        'course_title': course_title,
                        'department': department,
                        'section': "N/A",
                        'times': "N/A",
                        'location': "N/A",
                        'instructor': "N/A",
                        'credits': credits,
                        'enrollment': "N/A",
                        'description': description,
                        'url': page_url
                    }
                    courses.append(course_info)
                
            except Exception as e:
                print(f"Error parsing course: {e}")
                continue
                
        return courses

    async def scrape_department(self, url: str):
        """Scrape courses from a department page."""
        try:
            print(f"Navigating to: {url}")
            response = await self.page.goto(url)
            
            if not response:
                print(f"Failed to load {url}")
                return
            
            if response.status != 200:
                print(f"Error loading {url}: Status {response.status}")
                return
            
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle')
            
            # Get the page content
            html = await self.page.content()
            
            # Parse courses
            department_courses = self.parse_course_info(html, url)
            if department_courses:
                print(f"Found {len(department_courses)} courses in {url}")
                self.courses.extend(department_courses)
            else:
                print(f"No courses found in {url}")
                
        except TimeoutError:
            print(f"Timeout while loading {url}")
        except Exception as e:
            print(f"Error scraping department {url}: {e}")

    async def scrape_all_courses(self):
        """Main method to scrape all courses."""
        await self.setup()
        try:
            department_links = await self.get_department_links()
            if not department_links:
                print("No department links found. Exiting.")
                return
                
            print(f"Starting to scrape {len(department_links)} departments")
            
            for i, link in enumerate(department_links, 1):
                print(f"\nScraping department {i}/{len(department_links)}")
                await self.scrape_department(link)
                # Add a small delay between requests
                await asyncio.sleep(1)
                
            # Separate courses with valid course codes from those with "N/A"
            valid_courses = []
            invalid_courses = []
            
            for course in self.courses:
                if course['course_code'] == "N/A":
                    invalid_courses.append(course)
                else:
                    valid_courses.append(course)
            
            # Save valid courses to main CSV
            if valid_courses:
                df_valid = pd.DataFrame(valid_courses)
                df_valid.to_csv('columbia_courses.csv', index=False)
                print(f"\nSuccessfully scraped {len(valid_courses)} valid courses. Data saved to columbia_courses.csv")
            else:
                print("\nNo valid courses were scraped.")
            
            # Save invalid courses to separate CSV
            if invalid_courses:
                df_invalid = pd.DataFrame(invalid_courses)
                df_invalid.to_csv('columbia_courses_invalid.csv', index=False)
                print(f"Found {len(invalid_courses)} courses with invalid course codes. Data saved to columbia_courses_invalid.csv")
            else:
                print("No courses with invalid course codes found.")
                
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await self.close()

async def main():
    scraper = ColumbiaCourseScraper()
    await scraper.scrape_all_courses()

if __name__ == "__main__":
    asyncio.run(main()) 