# Import required libraries
from bs4 import BeautifulSoup
import requests
import re
import json 

# URL to scrape
url_requirements = "https://bulletin.columbia.edu/columbia-college/departments-instruction/mathematics/"

resp = requests.get(url_requirements)
soup = BeautifulSoup(resp.text, 'html.parser')

req_container = soup.find(id="requirementstextcontainer")
req_text = req_container.get_text(separator="\n").strip()

overview_container = soup.find(id="textcontainer")
overview_text = overview_container.get_text(separator="\n").strip()

with open('mathematics_major_overview.html', 'w', encoding='utf-8') as f:
    f.write(overview_container.prettify())

with open('mathematics_major_requirements.html', 'w', encoding='utf-8') as f:
    f.write(req_container.prettify())





