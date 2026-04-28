import sys
path = "/root/foodzuka/admin/resources/js/layouts/components/NavItems.vue"
with open(path, "rb") as f:
    data = f.read()

content = None
for enc in ['utf-8', 'cp1251', 'latin-1']:
    try:
        content = data.decode(enc)
        print(f"Decoded with {enc}")
        break
    except:
        continue

if content is None:
    print("Failed to decode")
    sys.exit(1)

lines = content.splitlines(keepends=True)
new_lines = []
for line in lines:
    if "/system/logs" in line or "/settings/sync-logs" in line:
        continue
    new_lines.append(line)
    if "settings/vk" in line:
        new_lines.append("    <VerticalNavLink :item=\"{ title: '\u041b\u043e\u0433\u0438 \u0441\u0438\u0441\u0442\u0435\u043c\u044b', to: '/system/logs' }\" />\n")
        new_lines.append("    <VerticalNavLink :item=\"{ title: '\u041b\u043e\u0433\u0438 \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u0438', to: '/settings/sync-logs' }\" />\n")

with open(path, "wb") as f:
    f.write("".join(new_lines).encode('utf-8'))
