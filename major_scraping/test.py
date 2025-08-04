# read mathematics_major.json file and see all the keys 

import json 

with open('mathematics_major.json', 'r') as f:
    data = json.load(f)

print(data.keys())