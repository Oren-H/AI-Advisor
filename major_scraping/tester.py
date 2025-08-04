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

url = "https://bulletin.columbia.edu/columbia-college/departments-instruction/computer-science/"

resp = requests.get(url)
soup = BeautifulSoup(resp.text, 'html.parser')

requirements_container = soup.find(id="requirementstextcontainer")

# save soup in an html file
with open("physics_requirements.html", "w") as f:
    f.write(requirements_container.prettify())
    
exit()