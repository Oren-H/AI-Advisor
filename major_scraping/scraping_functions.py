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
from bs4 import NavigableString

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
    for hdr in container.find_all("h2", class_="toggle"):
        title = clean_text(hdr.get_text())
        
        # skip any “major” / “minor” entries here
        if any(k in title.lower() for k in ("major", "minor", "concentration")):
            continue

        # collect all <p> until the next h2
        paras = []
        for sib in hdr.find_next_siblings():
            if sib.name == "h2" and "toggle" in (sib.get("class") or []):
                break
            if sib.name == "p":
                txt = clean_text(sib.get_text())
                if txt:
                    paras.append(txt)

        # if this h2 has no paras, try to find h3 subsections
        if not paras:
            child_secs = []
            for sib in hdr.find_next_siblings():
                if sib.name == "h2" and "toggle" in (sib.get("class") or []):
                    break
                if sib.name == "h3" and "toggle" in (sib.get("class") or []):
                    sub_title = clean_text(sib.get_text())
                    # collect its paragraphs
                    sub_paras = []
                    for ps in sib.find_next_siblings():
                        if ps.name in ("h2","h3") and "toggle" in (ps.get("class") or []):
                            break
                        if ps.name == "p":
                            t = clean_text(ps.get_text())
                            if t:
                                sub_paras.append(t)
                    if sub_paras:
                        child_secs.append({
                            "section_name": sub_title,
                            "paragraphs": sub_paras
                        })
            if child_secs:
                sections.append({
                    "section_name": title,
                    "subsections": child_secs
                })
            # if no paras *and* no subsections, we simply skip it
        else:
            sections.append({
                "section_name": title,
                "paragraphs": paras
            })

    return sections

def parse_table(tbl: Tag, include_html: bool = False):
    """
    Return either:
      - if include_html=False: list-of-lists of cell‐texts
      - if include_html=True: dict with 'rows' and 'html'
    """
    if tbl is None:
        return None
    
    rows = []
    for tr in tbl.select("tbody tr"):
        cells = [clean_text(td.get_text(" ")) for td in tr.find_all(["td","th"])]
        rows.append(cells)

    if include_html:
        return {
            "rows": rows,
            "html": str(tbl)
        }
    else:
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

    # 1) Department code (first courseblocktitle fallback)
    course_block = soup.find(class_="courseblocktitle")
    if course_block:
        department_code = course_block.text.strip()[:4]
    else:
        department_code = "UNKN"

    # 2) Overview sections (unchanged)
    overview_container = soup.find(id="textcontainer")
    if overview_container:
        dept_name = clean_text(
            overview_container.find("h2", class_="toggle").get_text()
        )
        overview_sections = build_sections(overview_container)
    else:
        dept_name = department_name or "Unknown Department"
        overview_sections = []

    # 3) Department-wide requirements (unchanged)
    requirements_container = soup.find(id="requirementstextcontainer")
    if requirements_container:
        department_wide_requirements = build_sections(requirements_container)
    else:
        department_wide_requirements = []

    # 4) One-pass grouping of every child under #requirementstextcontainer
    blocks = []
    if requirements_container:
        for child in requirements_container.find_all(recursive=False):
            # start a new block at each <h2>/<h3 class="toggle">
            if child.name in ("h2","h3") and "toggle" in (child.get("class") or []):
                blocks.append({"header": child, "nodes": []})
            elif blocks:
                blocks[-1]["nodes"].append(child)

    # 5) Extract JUST the Major/Minor blocks
    majors = {}
    counter = 1
    for blk in blocks:
        title = clean_text(blk["header"].get_text())
        if "major" not in title.lower() and "minor" not in title.lower():
            continue

        major_id = f"{department_code}{counter}"
        counter += 1

        # re-serialize header + all its nodes into one <div class="toggle-wrap">
        html_snippet = ['<div class="toggle-wrap">']
        html_snippet.append(str(blk["header"]))
        for node in blk["nodes"]:
            html_snippet.append(str(node))
        html_snippet.append("</div>")

        majors[major_id] = {
            "major_name":    title,
            "major_html":    "\n".join(html_snippet),
            "course_lists":  [],
            "cognates":      [],
            "footnotes":     []
        }

        # now pull out tables & footnotes from blk["nodes"]
        for node in blk["nodes"]:
            if node.name == "table" and "sc_courselist" in node.get("class", []):
                majors[major_id]["course_lists"].append(
                    parse_table(node, include_html=False)
                )
            elif node.name == "table" and "sc_prerequisite" in node.get("class", []):
                majors[major_id]["cognates"].append(
                    parse_table(node, include_html=False)
                )
            elif node.name == "dl" and "sc_footnotes" in node.get("class", []):
                notes = [ clean_text(dd.get_text(" ")) for dd in node.find_all("dd") ]
                majors[major_id]["footnotes"].extend(notes)
        
        toggle = blk["header"]
        toggle_text = ""
        for sib in toggle.find_next_siblings():
            if sib.name in ("h2","h3") and "toggle" in (sib.get("class") or []):
                break
            if isinstance(sib, Tag):
                text = clean_text(sib.get_text())
                if text:
                    toggle_text += text

        if not majors[major_id]["course_lists"]:
            if department_code not in toggle_text:
                del majors[major_id]
                counter -= 1
            else: 
                majors[major_id]["course_lists"] = toggle_text 

    # 6) Bundle into final structure
    comprehensive_data = {
        "department_code":             department_code,
        "department_name":             dept_name,
        "website":                     url,
        "overview_sections":           overview_sections,
        "department_wide_requirements":department_wide_requirements,
        "majors":                      majors
    }

    return comprehensive_data


def save_comprehensive_json(data, filename):
    """Save the comprehensive data to a JSON file."""
    with open(f"major_scraping/data/{filename}", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved comprehensive data to: {filename}")

def main():
    """Main function to run the scraper."""
    # Default URL for mathematics (can be overridden)
    url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/computer-science/"
    
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
    
        
    except Exception as e:
        print(f"Error scraping department: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())