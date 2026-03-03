import urllib.request
import json
req = urllib.request.urlopen("http://localhost:8000/api/config/hierarchy/tree")
data = json.loads(req.read())
for child in data[0]["children"]:
    if child["tag"] == "T73-FT-5801":
        print(f"Curl Meter: {child['tag']}")
        print(f"Curl Children: {[c['tag'] for c in child['children']]}")
