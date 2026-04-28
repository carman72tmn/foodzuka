import json
import os

with open('/app/scratch/menu_68484.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stats = {
    "total_categories": len(data.get('itemCategories', [])),
    "total_items": 0,
    "items_with_multiple_sizes": 0,
    "items_with_modifiers": 0,
    "max_sizes": 0,
    "max_modifiers": 0
}

for cat in data.get('itemCategories', []):
    for i in cat.get('items', []):
        stats["total_items"] += 1
        sizes = i.get('itemSizes', [])
        mods = []
        for s in sizes:
            mods.extend(s.get('itemModifierGroups', []))
        
        if len(sizes) > 1:
            stats["items_with_multiple_sizes"] += 1
            stats["max_sizes"] = max(stats["max_sizes"], len(sizes))
        
        if mods:
            stats["items_with_modifiers"] += 1
            stats["max_modifiers"] = max(stats["max_modifiers"], len(mods))

print(json.dumps(stats, indent=2))
