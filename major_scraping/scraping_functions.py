# Import required libraries
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
import json
import sys
import os

def clean_text(text: str) -> str:
    """Collapse whitespace and strip."""
    text = text.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def build_sections(container, exclude_titles=None,):
    """
    Build sections from plain <h2> and <h3> tags.
    If exclude_titles is a list of lowercase substrings, skip any <h2>
    whose title contains one of those substrings.
    """
    exclude_titles = [e.lower() for e in (exclude_titles or [])]

    sections = []
    for hdr in container.find_all("h2", recursive=False):
        title = clean_text(hdr.get_text())

        # <-- skip unwanted titles when requested
        if any(ex in title.lower() for ex in exclude_titles):
            continue

        paras = []
        subsections = []
        current_sub = None

        for sib in hdr.next_siblings:
            if isinstance(sib, Tag) and sib.name == "h2":
                break
            if isinstance(sib, Tag):
                if sib.name == "p":
                    txt = clean_text(sib.get_text())
                    if not txt:
                        continue
                    if current_sub:
                        current_sub["paragraphs"].append(txt)
                    else:
                        paras.append(txt)
                elif sib.name == "h3":
                    sub_title = clean_text(sib.get_text())
                    if any(ex in sub_title.lower() for ex in exclude_titles):
                        continue 
                    current_sub = {"section_name": sub_title, "paragraphs": []}
                    subsections.append(current_sub)

        if subsections and not paras:
            sections.append({
                "section_name": title,
                "subsections": subsections
            })
        elif paras:
            sections.append({
                "section_name": title,
                "paragraphs": paras
            })
    
    return sections

def parse_table(tbl: Tag, include_html: bool = False):
    if tbl is None:
        return None
    rows = []
    for tr in tbl.select("tbody tr"):
        cells = [clean_text(td.get_text(" ")) for td in tr.find_all(["td","th"])]
        rows.append(cells)
    if include_html:
        return {"rows": rows, "html": str(tbl)} # TODO: remove this
    else:
        return rows

def scrape_department(url):
    print(f"Scraping department from: {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # 1) Department code and name from URL
    course_block = soup.find(class_="courseblocktitle")
    department_code = course_block.text.strip()[:4] if course_block else "UNKN"

    # Extract department name from URL pattern: .../departments-instruction/{dept_name}/
    import re
    url_match = re.search(r'/departments-instruction/([^/]+)/', url)
    department_name_from_url = url_match.group(1) if url_match else "unknown"
    print(department_name_from_url)

    if department_code == "UNKN" and department_name_from_url != "unknown":
        department_code = department_name_from_url

    # 2) Overview sections (no exclusions)
    overview_container = soup.find(id="textcontainer")
    if overview_container:
        first_h2 = overview_container.find("h2", recursive=False)
        dept_name = department_name_from_url
        overview_sections = build_sections(overview_container)
    else:
        dept_name = department_name_from_url
        overview_sections = []

    # 3) Department-wide requirements: exclude any "major"/"minor"/"concentration"
    requirements_container = soup.find(id="requirementstextcontainer")
    if requirements_container:
        department_wide_requirements = build_sections(
            requirements_container,
            exclude_titles=["major", "minor", "concentration"]
        )
    else:
        department_wide_requirements = []

    # 4) Group direct children under requirements
    blocks = []
    if requirements_container:
        for child in requirements_container.find_all(recursive=False):
            if isinstance(child, Tag) and child.name in ("h2", "h3"):
                blocks.append({"header": child, "nodes": []})
            elif blocks and isinstance(child, Tag):
                blocks[-1]["nodes"].append(child)

    # 5) Extract majors/minors blocks
    majors = {}
    counter = 1
    for blk in blocks:
        title = clean_text(blk["header"].get_text())
        if "major" not in title.lower() and "minor" not in title.lower():
            continue

        major_id = f"{department_code}{counter}"
        counter += 1

        # html_snippet = ['<div class="toggle-wrap">', str(blk["header"])]
        # html_snippet += [str(node) for node in blk["nodes"]]
        # html_snippet.append("</div>")

        majors[title] = {
            "major_id":   major_id,
            "course_lists": [],
            "cognates":     [],
            "footnotes":    []
        }

        toggle_text = ""
        for node in blk["nodes"]:
            if node.name == "table" and "sc_courselist" in node.get("class", []):
                majors[title]["course_lists"].append(parse_table(node))
            elif node.name == "table" and "sc_prerequisite" in node.get("class", []):
                majors[title]["cognates"].append(parse_table(node))
            elif node.name == "dl" and "sc_footnotes" in node.get("class", []):
                notes = [clean_text(dd.get_text(" ")) for dd in node.find_all("dd")]
                majors[title]["footnotes"].extend(notes)

            text = clean_text(node.get_text())
            if text:
                toggle_text += text

        # **Fix here**: only drop blocks when dept_code is known and missing from text
        if not majors[title]["course_lists"]:
            if department_code != "UNKN" and department_code not in toggle_text:
                del majors[title]
                counter -= 1
            else:
                majors[title]["course_lists"] = toggle_text

    # 6) Bundle final structure - keyed by department code
    comprehensive_data = {
        department_code: {
            "department_name":              dept_name,
            "website":                      url,
            "overview_sections":            overview_sections,
            "department_wide_requirements": department_wide_requirements,
            "majors":                       majors
        }
    }

    return comprehensive_data

def save_comprehensive_json(data, filename):
    os.makedirs("major_scraping/data", exist_ok=True)
    with open(f"major_scraping/data/{filename}", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved comprehensive data to: {filename}")

def main():
    url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/computer-science/"
    if len(sys.argv) > 1:
        url = sys.argv[1]

    try:
        data = scrape_department(url)
        # Get department code from the keys (since data is now keyed by dept code)
        dept_code = list(data.keys())[0]
        filename = f"{dept_code.lower()}_comprehensive.json"
        save_comprehensive_json(data, filename)
    except Exception as e:
        print(f"Error scraping department: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
