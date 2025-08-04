#!/usr/bin/env python3
"""
Example script to demonstrate the generalizable department scraper.
This script shows how to scrape different departments and create the comprehensive JSON structure.
"""

from scraping_math import scrape_department, save_comprehensive_json
import json

def main():
    """Example usage of the department scraper."""
    
    # Example departments to scrape
    departments = [
        {
            "name": "Mathematics",
            "url": "https://bulletin.columbia.edu/columbia-college/departments-instruction/mathematics/"
        },
        {
            "name": "Computer Science", 
            "url": "https://bulletin.columbia.edu/columbia-college/departments-instruction/computer-science/"
        },
        {
            "name": "Physics",
            "url": "https://bulletin.columbia.edu/columbia-college/departments-instruction/physics/"
        }
    ]
    
    print("Starting department scraping...")
    
    for dept in departments:
        print(f"\n{'='*50}")
        print(f"Scraping {dept['name']} department...")
        print(f"{'='*50}")
        
        try:
            # Scrape the department
            data = scrape_department(dept['url'], dept['name'])
            
            # Save comprehensive JSON
            filename = f"{data['department_code'].lower()}_comprehensive.json"
            save_comprehensive_json(data, filename)
            
            # Print summary
            print(f"Department: {data['department_name']}")
            print(f"Code: {data['department_code']}")
            print(f"Overview sections: {len(data['overview_sections'])}")
            print(f"Requirements sections: {len(data['requirements_sections'])}")
            print(f"Majors/Minors: {len(data['majors'])}")
            
            # List the majors
            for major_id, major_data in data['majors'].items():
                print(f"  - {major_id}: {major_data['major_name']}")
            
        except Exception as e:
            print(f"Error scraping {dept['name']}: {e}")
            continue
    
    print(f"\n{'='*50}")
    print("Scraping completed!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
        