import json
import os

with open('/app/scratch/menu_68484.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Items with multiple sizes or modifiers:")
found = 0
for cat in data.get('itemCategories', []):
    for i in cat.get('items', []):
        sizes = i.get('itemSizes', [])
        mods = i.get('itemModifierGroups', [])
        if len(sizes) > 1 or mods:
            print(f"Item: {i.get('name')} (ID: {i.get('itemId')})")
            print(f"  Sizes ({len(sizes)}):")
            for s in sizes:
                print(f"    - {s.get('sizeName')} (ID: {s.get('sizeId')}) Prices: {s.get('prices')}")
            print(f"  Modifier Groups ({len(mods)}):")
            for mg in mods:
                print(f"    - {mg.get('name')} (ID: {mg.get('modifierGroupId')}) Min: {mg.get('minAmount')} Max: {mg.get('maxAmount')}")
                for mi in mg.get('items', []):
                     print(f"        - {mi.get('name')} (ID: {mi.get('itemId')}) Prices: {mi.get('prices')}")
            found += 1
            if found > 10:
                break
    if found > 10:
        break
