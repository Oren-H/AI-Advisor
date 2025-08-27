import json

def generate_major_context(department_of_major: str, major: str) -> str:
    """Generate a context for a major."""
    # given a major, generate a context for the major from all_departments.json
    with open('all_departments.json', 'r') as f:
        departments_data = json.load(f)

    
    if department_data['department_code'].lower() == department_of_major.lower():
        return 
    

    return f"I don't have information about the {major} major."
   



if __name__ == "__main__":
    print(generate_major_context("Applied Mathematics"))



