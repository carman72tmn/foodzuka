import json
import os

with open('/app/scratch/menu_68484.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Keys: {list(data.keys())}")
if 'itemCategories' in data:
    print(f"ItemCategories count: {len(data['itemCategories'])}")
    for cat in data['itemCategories']:
        items = cat.get('items', [])
        print(f"Category: {cat.get('name')} (ID: {cat.get('id')}) - Items count: {len(items)}")
        if items:
            item = items[0]
            print(f"  Item example: {item.get('name')} (ID: {item.get('itemId')})")
            print(f"    Keys: {list(item.keys())}")
            if 'itemSizes' in item:
                print(f"    itemSizes count: {len(item['itemSizes'])}")
                for s in item['itemSizes']:
                    print(f"      Size: {s.get('sizeName')} (ID: {s.get('sizeId')})")
            if 'itemModifierGroups' in item:
                print(f"    itemModifierGroups count: {len(item['itemModifierGroups'])}")
                for mg in item['itemModifierGroups']:
                    print(f"      ModGroup: {mg.get('name')} (ID: {mg.get('modifierGroupId')})")
                    for m in mg.get('items', []):
                         print(f"        - {m.get('name')} (ID: {m.get('itemId')})")
            break
