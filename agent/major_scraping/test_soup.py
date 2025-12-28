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

url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/regional-studies/"

resp = requests.get(url)
soup = BeautifulSoup(resp.text, 'html.parser')

requirements_container = soup.find(id="requirementstextcontainer")
overview_container = soup.find(id="textcontainer")

# save soup in an html file
with open("regional_studies_overview.html", "w") as f:
    f.write(overview_container.prettify())

with open("regional_studies_requirements.html", "w") as f:
    f.write(requirements_container.prettify())

exit()