import asyncio
import json
import time
from urllib.parse import urljoin

from playwright.async_api import async_playwright, TimeoutError
import scraping_functions as sf

class AllDepartmentsScraper:
    def __init__(self):
        self.base_url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/"
        self.link_selector = 'a'

    async def setup(self):
        """Initialize Playwright for dynamic link extraction."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)

    async def get_department_links(self) -> list:
        """Fetch and return all unique department URLs."""
        await self.page.goto(self.base_url)
        await self.page.wait_for_selector(self.link_selector)
        anchors = await self.page.query_selector_all(self.link_selector)
        links = set()
        for a in anchors:
            href = await a.get_attribute('href')
            if href and '/departments-instruction/' in href and href != self.base_url:
                absolute = urljoin(self.base_url, href)
                links.add(absolute)
        return sorted(links)

    async def cleanup(self):
        """Close Playwright resources."""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

async def main():
    scraper = AllDepartmentsScraper()
    await scraper.setup()
    print("Fetching department links...")
    dept_links = await scraper.get_department_links()
    print(f"Found {len(dept_links)} department links.")
    
    all_departments = {}
    for i, url in enumerate(dept_links, 1):
        if url == "https://bulletin.columbia.edu/columbia-college/departments-instruction/search":
            continue

        print(f"[{i}/{len(dept_links)}] Scraping: {url}")
        try:
            # Use scrape_department from scraping_functions.py
            data = sf.scrape_department(url)
            # Add timestamp to each department's data
            for dept_code in data:
                data[dept_code]['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            # Merge into main dictionary
            all_departments.update(data)
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    await scraper.cleanup()

    # Save collected data
    output_file = 'major_scraping/data/major_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_departments, f, indent=2, ensure_ascii=False)
    print(f"Scraped data for {len(all_departments)} departments saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())

