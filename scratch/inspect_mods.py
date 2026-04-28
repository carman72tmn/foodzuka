import json
import os

with open('/app/scratch/menu_68484.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for cat in data.get('itemCategories', []):
    for i in cat.get('items', []):
        sizes = i.get('itemSizes', [])
        for s in sizes:
            mods = s.get('itemModifierGroups', [])
            if mods:
                print(f"Item with mods: {i.get('name')}")
                print(f"  Size: {s.get('sizeName')}")
                print(f"  ModGroups: {[mg.get('name') for mg in mods]}")
                for mg in mods:
                    print(f"    Group: {mg.get('name')} (ID: {mg.get('modifierGroupId')})")
                    for mi in mg.get('items', []):
                        print(f"      - {mi.get('name')} (ID: {mi.get('itemId')})")
                break
        else: continue
        break
    else: continue
    break
