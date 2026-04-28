import sys
path = "/root/foodzuka/admin/resources/js/pages/settings/iiko.vue"
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

# Add ref
content = content.replace("const showPassword = ref(false)", "const showPassword = ref(false)\nconst showWebhookToken = ref(false)")

# Replace field
old_field = '<VTextField v-model="settings.webhook_auth_token" label="Токен авторизации" class="mb-4" />'
new_field = '''<VTextField 
                    v-model="settings.webhook_auth_token" 
                    label="Токен авторизации" 
                    class="mb-4"
                    :type="showWebhookToken ? 'text' : 'password'"
                    :append-inner-icon="showWebhookToken ? 'bx-hide' : 'bx-show'"
                    @click:append-inner="showWebhookToken = !showWebhookToken"
                  />'''

content = content.replace(old_field, new_field)

with open(path, "wb") as f:
    f.write(content.encode('utf-8'))
