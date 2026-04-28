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

# Add Regional Settings card if not present
if "Региональные настройки" not in content:
    regional_card = """
            <VCol cols="12" md="6">
              <VCard class="h-100" title="Региональные настройки">
                <VCardText>
                  <VTextField
                    v-model="settings.timezone_name"
                    label="Часовой пояс (напр. Asia/Yekaterinburg)"
                    class="mb-4"
                  />
                  <VSelect
                    v-model="settings.address_format"
                    :items="[
                      { title: 'Компоненты (Город, Улица, Дом)', value: 'components' },
                      { title: 'Стандартный (Строка)', value: 'standard' }
                    ]"
                    label="Формат адреса для iiko"
                    class="mb-4"
                  />
                  <VTextField
                    v-model="settings.city_name"
                    label="Город по умолчанию"
                  />
                </VCardText>
              </VCard>
            </VCol>
"""
    # Find the end of the first Row in general tab
    # Looking for the button "Сохранить всё"
    marker = '@click="saveSettings"'
    if marker in content:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if marker in line and "VBtn" in line:
                # Find the VCol that contains this button
                for j in range(i, 0, -1):
                    if "<VCol" in lines[j]:
                        lines.insert(j, regional_card)
                        break
                break
        content = "\n".join(lines)

with open(path, "wb") as f:
    f.write(content.encode('utf-8'))
