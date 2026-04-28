import json
import os

with open('/app/scratch/menu_68484.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for cat in data.get('itemCategories', []):
    for i in cat.get('items', []):
        if i.get('name') == 'Ёсан Кани':
            print(json.dumps(i, indent=2, ensure_ascii=False))
            break
    else: continue
    break
