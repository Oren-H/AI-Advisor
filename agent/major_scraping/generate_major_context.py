import json
from difflib import get_close_matches
from typing import Dict, Any, Optional

def generate_major_context(department_of_major: str, major: str) -> Dict[str, Any]:
    """Generate a context for a major with fuzzy matching and error handling."""
    try:
        with open('major_scraping/data/major_data.json', 'r') as f:
            all_departments_data = json.load(f)
        
        # Handle missing department
        if department_of_major not in all_departments_data:
            # Try fuzzy matching for department
            dept_matches = get_close_matches(
                department_of_major, 
                list(all_departments_data.keys()), 
                n=1, cutoff=0.6
            )
            if dept_matches:
                department_of_major = dept_matches[0]
                print(f"🔍 Fuzzy matched department: {department_of_major}")
            else:
                raise ValueError(f"Department '{department_of_major}' not found")
        
        department_data = all_departments_data[department_of_major]
        
        # Handle missing major with fuzzy matching
        if major not in department_data['majors']:
            major_matches = get_close_matches(
                major,
                list(department_data['majors'].keys()),
                n=1, cutoff=0.6
            )
            if major_matches:
                major = major_matches[0] 
                print(f"🔍 Fuzzy matched major: {major}")
            else:
                available_majors = list(department_data['majors'].keys())
                raise ValueError(f"Major '{major}' not found in {department_of_major}. Available majors: {available_majors}")

        
        # Return focused context - target major + essential department info only
        return {
            "department_code": department_of_major,
            "department_name": department_data.get('department_name', ''),
            "major_name": major,
            "major_requirements": major_data,
            "department_overview": department_data.get('overview_sections', []),
            "department_requirements": department_data.get('department_wide_requirements', [])
        }
        
    except FileNotFoundError:
        raise ValueError("Major data file not found. Please ensure major_data.json exists.")
    except KeyError as e:
        raise ValueError(f"Data structure error: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error generating major context: {str(e)}")
    
if __name__ == "__main__":
    print(generate_major_context("MATH", "Major in Mathematics"))



