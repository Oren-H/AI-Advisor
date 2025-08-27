import json

def generate_major_context(department_of_major: str, major: str) -> str:
    """Generate a context for a major."""
    # given a major, generate a context for the major from all_departments.json
    with open('major_scraping/data/major_data.json', 'r') as f:
        all_departments_data = json.load(f)
    
    
    department_data = all_departments_data[department_of_major]    
    major_data = department_data['majors'][major]
    return major_data
    
if __name__ == "__main__":
    print(generate_major_context("MATH", "Major in Mathematics"))



