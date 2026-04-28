import sys
path = "/root/foodzuka/admin/resources/js/pages/orders/index.vue"
with open(path, "rb") as f:
    data = f.read()

content = None
for enc in ['utf-8', 'cp1251', 'latin-1']:
    try:
        content = data.decode(enc)
        break
    except:
        continue

if content is None:
    sys.exit(1)

# Replace status colors and names access with lowercase version
content = content.replace(":color=\"statusColors[item.status] || 'grey'\"", ":color=\"statusColors[item.status?.toLowerCase()] || 'grey'\"")
content = content.replace("{{ statusNames[item.status] || item.status }}", "{{ statusNames[item.status?.toLowerCase()] || item.status }}")

with open(path, "wb") as f:
    f.write(content.encode('utf-8'))
