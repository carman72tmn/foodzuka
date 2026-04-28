import json
import os

with open('/app/scratch/menu_68484.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for cat in data.get('itemCategories', []):
    print(f"Category: {cat.get('name')}")
    for i in cat.get('items', []):
        print(f"Item: {i.get('name')} (ID: {i.get('itemId')})")
        print(f"  Keys: {list(i.keys())}")
        sizes = i.get('itemSizes', [])
        print(f"  Sizes count: {len(sizes)}")
        for s in sizes:
            print(f"    Size: {s.get('sizeName')} Keys: {list(s.keys())}")
            if 'itemModifierGroups' in s:
                print(f"      Modifier Groups in Size: {len(s['itemModifierGroups'])}")
        if 'itemModifierGroups' in i:
            print(f"  Modifier Groups in Item: {len(i['itemModifierGroups'])}")
        break
    break
