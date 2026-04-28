import sys
path = "/root/foodzuka/admin/resources/js/plugins/vuetify/index.js"
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

# Add ru locale import
if "import { ru } from 'vuetify/locale'" not in content:
    content = content.replace("import { createVuetify } from 'vuetify'", "import { createVuetify } from 'vuetify'\nimport { ru } from 'vuetify/locale'")

# Add locale config to createVuetify
if "locale:" not in content:
    content = content.replace("theme: {", "locale: {\n      locale: 'ru',\n      fallback: 'en',\n      messages: { ru },\n    },\n    theme: {")

with open(path, "wb") as f:
    f.write(content.encode('utf-8'))
