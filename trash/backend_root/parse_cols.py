import json

with open('out.txt', 'r') as f:
    content = f.read()
    # Skip logs
    json_start = content.find('{')
    if json_start != -1:
        data = json.loads(content[json_start:])
        for key, val in data.items():
            print(f"{key}: {val.get('name')}")
