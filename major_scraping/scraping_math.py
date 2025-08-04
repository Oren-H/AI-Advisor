# Import required libraries
from bs4 import BeautifulSoup
import requests
import re
import json
import pandas as pd 
import numpy as np 
from bs4 import BeautifulSoup
from bs4.element import Tag 
import pprint
import sys
import os

def clean_text(text: str) -> str:
    """Collapse whitespace and strip."""
    text = text.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def extract_block(header_tag):
    """
    Collect all <p> siblings until the next <h2> or <h3>.
    Returns a list of cleaned paragraph strings.
    """
    paras = []
    for sib in header_tag.find_next_siblings():
        if sib.name in ('h2','h3') and 'toggle' in (sib.get('class') or []):
            break
        if sib.name == 'p':
            txt = clean_text(sib.get_text())
            if txt:
                paras.append(txt)
    return paras

def build_sections(container):
    """Build sections structure for overview and requirements text."""
    sections = []
    for hdr in container.find_all(["h2","h3"], class_="toggle"):
        title = clean_text(hdr.get_text())
        if "major" in title.lower() or "minor" in title.lower() or "concentration" in title.lower():
            continue

        paras = extract_block(hdr)

        # Case A: H2 with no paras but with H3 children -> subsections
        if hdr.name == "h2" and not paras:
            child_sections = []
            for sib in hdr.find_next_siblings():
                # stop at next H2
                if sib.name == "h2" and "toggle" in (sib.get("class") or []):
                    break
                if sib.name == "h3" and "toggle" in (sib.get("class") or []):
                    sub_title = clean_text(sib.get_text())
                    sub_paras = extract_block(sib)
                    if sub_paras:
                        child_sections.append({
                            "section_name": sub_title,
                            "paragraphs": sub_paras
                        })
            if child_sections:
                sections.append({
                    "section_name": title,
                    "subsections": child_sections
                })
            continue

        # Case B: normal header with its own paragraphs
        if paras:
            sections.append({
                "section_name": title,
                "paragraphs": paras
            })

    return sections

def parse_table(tbl: Tag):
    """Return a list-of-lists of cell‐texts for a <table>."""
    rows = []
    for tr in tbl.select("tbody tr"):
        cells = [clean_text(td.get_text(" ")) for td in tr.find_all(["td","th"])]
        rows.append(cells)
    return rows

def scrape_department(url, department_name=None):
    """
    Scrape a department page and return comprehensive JSON structure.
    
    Args:
        url: The department URL to scrape
        department_name: Optional department name override
    
    Returns:
        Dictionary with the comprehensive structure
    """
    print(f"Scraping department from: {url}")
    
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find department code from course block
    course_block = soup.find(class_="courseblocktitle")
    if course_block:
        department_code = str(course_block.text)[:4]
    else:
        # Fallback: try to extract from URL or use a default
        department_code = "UNKN"

    # Get overview sections
    overview_container = soup.find(id="textcontainer")
    if overview_container:
        dept_name = clean_text(overview_container.find("h2", class_="toggle").get_text())
        overview_sections = build_sections(overview_container)
    else:
        dept_name = department_name or "Unknown Department"
        overview_sections = []

    # Get requirements sections
    requirements_container = soup.find(id="requirementstextcontainer")
    if requirements_container:
        requirements_sections = build_sections(requirements_container)
    else:
        requirements_sections = []

    # Parse majors and minors
    majors = {}
    if requirements_container:
        counter = 1
        for toggle in requirements_container.find_all("h2", class_="toggle"):
            title = clean_text(toggle.get_text())
            if "major" not in title.lower() and "minor" not in title.lower():
                continue

            major_id = f"{department_code}{counter}"
            counter += 1

            majors[major_id] = {
                "major_name": title,
                "course_lists": [],
                "prerequisites": [],
                "footnotes": []
            }

            # Walk forward through siblings until the next <h2 class="toggle">
            for sib in toggle.next_siblings:
                if isinstance(sib, Tag) and sib.name=="h2" and "toggle" in sib.get("class", []):
                    break

                if isinstance(sib, Tag):
                    # 1) course lists
                    if sib.name=="table" and "sc_courselist" in sib.get("class", []):
                        majors[major_id]["course_lists"].append(parse_table(sib))

                    # 2) prerequisites
                    elif sib.name=="table" and "sc_prerequisite" in sib.get("class", []):
                        majors[major_id]["prerequisites"].append(parse_table(sib))

                    # 3) footnotes
                    elif sib.name=="dl" and "sc_footnotes" in sib.get("class", []):
                        notes = [clean_text(dd.get_text(" ")) for dd in sib.find_all("dd")]
                        majors[major_id]["footnotes"].extend(notes)

    # Build the comprehensive structure
    comprehensive_data = {
        "department_code": department_code,
        "department_name": dept_name,
        "website": url,
        "overview_sections": overview_sections,
        "department_wide_requirements": requirements_sections,
        "majors": majors
    }

    return comprehensive_data

def save_comprehensive_json(data, filename):
    """Save the comprehensive data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved comprehensive data to: {filename}")

def main():
    """Main function to run the scraper."""
    # Default URL for mathematics (can be overridden)
    url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/mathematics/"
    
    # Check if URL is provided as command line argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    # Check if department name is provided
    department_name = None
    if len(sys.argv) > 2:
        department_name = sys.argv[2]
    
    try:
        # Scrape the department
        data = scrape_department(url, department_name)
        
        # Generate filename based on department code
        filename = f"{data['department_code'].lower()}_comprehensive.json"
        
        # Save the comprehensive data
        save_comprehensive_json(data, filename)
        
        # # Also save individual files for backward compatibility
        # overview_data = {
        #     "dept_code": data["department_code"],
        #     "name": data["department_name"],
        #     "website": data["website"],
        #     "sections": data["overview_sections"]
        # }
        
        # requirements_text_data = {
        #     "dept_code": data["department_code"],
        #     "name": data["department_name"],
        #     "website": data["website"],
        #     "sections": data["requirements_sections"]
        # }
        
        # # Save individual files
        # overview_filename = f"{data['department_code'].lower()}_major_overview.json"
        # requirements_filename = f"{data['department_code'].lower()}_major_requirement_text.json"
        # majors_filename = f"{data['department_code'].lower()}_major_requirements.json"
        
        # with open(overview_filename, 'w', encoding='utf-8') as f:
        #     json.dump(overview_data, f, ensure_ascii=False, indent=2)
        
        # with open(requirements_filename, 'w', encoding='utf-8') as f:
        #     json.dump(requirements_text_data, f, ensure_ascii=False, indent=2)
        
        # with open(majors_filename, 'w', encoding='utf-8') as f:
        # #     json.dump(data["majors"], f, ensure_ascii=False, indent=2)
        
        # print(f"Saved individual files:")
        # print(f"  - {overview_filename}")
        # print(f"  - {requirements_filename}")
        # print(f"  - {majors_filename}")
        
    except Exception as e:
        print(f"Error scraping department: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

     





