import re

p = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\admin\resources\js\pages\marketing\vk-bots.vue"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

dialogs = re.findall(r'<VDialog[^>]*v-model="([^"]+)"', text)
print("Dialog models found:", set(dialogs))
