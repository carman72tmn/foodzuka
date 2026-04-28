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

# Add timezone fields to settings ref
if "timezone_name" not in content:
    content = content.replace("price_category_id: \"\",", "price_category_id: \"\",\n  timezone_name: \"\",\n  manual_timezone: \"\",\n  address_format: \"standard\",\n  city_name: \"\",")

# Add Regional Settings card
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
            </VCol>"""

if "Региональные настройки" not in content:
    # Insert after the "Дополнительно" card
    content = content.replace("</VCard>\n            </VCol>\n\n            <VCol cols=\"12\" class=\"mt-4\">", 
                             "</VCard>\n            </VCol>\n" + regional_card + "\n\n            <VCol cols=\"12\" class=\"mt-4\">")

with open(path, "wb") as f:
    f.write(content.encode('utf-8'))
