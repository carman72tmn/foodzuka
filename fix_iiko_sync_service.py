
import sys
import os

file_path = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\iiko_sync_service.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def find_block(lines, start_text, end_text):
    start_idx = -1
    for i, line in enumerate(lines):
        if start_text in line:
            start_idx = i
            break
    if start_idx == -1: return -1, -1
    
    end_idx = -1
    for i in range(start_idx, len(lines)):
        if end_text in lines[i].strip():
            end_idx = i
            break
    return start_idx, end_idx

# 1. format_address
s1, e1 = find_block(lines, "def format_address", "return \", \".join(parts)")
if s1 != -1 and e1 != -1:
    new_format = [
        "    def format_address(self, addr_obj: Dict[str, Any], city: Optional[str] = None, fmt: str = \"components\") -> str:\n",
        "        \"\"\"\n",
        "        Универсальное форматирование адреса из объекта iiko.\n",
        "        fmt: 'components' (собрать из полей) или 'line1' (использовать готовую строку)\n",
        "        \"\"\"\n",
        "        if not addr_obj or not isinstance(addr_obj, dict):\n",
        "            return city or \"Тюмень\"\n",
        "\n",
        "        clean = self.clean_str\n",
        "        \n",
        "        # Извлекаем компоненты\n",
        "        s_obj = addr_obj.get(\"street\")\n",
        "        street = None\n",
        "        if isinstance(s_obj, dict):\n",
        "            street = clean(s_obj.get(\"name\"))\n",
        "        else:\n",
        "            street = clean(s_obj)\n",
        "\n",
        "        # Игнорируем плейсхолдеры\n",
        "        if street and all(char in \"-. \" for char in street):\n",
        "            street = None\n",
        "            \n",
        "        house = clean(addr_obj.get(\"house\"))\n",
        "        if house and all(char in \"-. \" for char in house): house = None\n",
        "        \n",
        "        flat = clean(addr_obj.get(\"flat\"))\n",
        "        if flat and all(char in \"-. \" for char in flat): flat = None\n",
        "        \n",
        "        entrance = clean(addr_obj.get(\"entrance\"))\n",
        "        floor = clean(addr_obj.get(\"floor\"))\n",
        "        doorphone = clean(addr_obj.get(\"doorphone\"))\n",
        "\n",
        "        # Город\n",
        "        city_from_obj = clean(addr_obj.get(\"city\"))\n",
        "        if not city_from_obj and isinstance(addr_obj.get(\"city\"), dict):\n",
        "            city_from_obj = clean(addr_obj.get(\"city\").get(\"name\"))\n",
        "        \n",
        "        final_city = city_from_obj or city or \"Тюмень\"\n",
        "\n",
        "        # Если выбран формат line1, пробуем его\n",
        "        if fmt == \"line1\":\n",
        "            l1 = clean(addr_obj.get(\"line1\") or addr_obj.get(\"addressString\"))\n",
        "            # Если line1 содержит больше чем просто город, возвращаем его\n",
        "            if l1 and len(l1) > len(final_city) + 2 and not all(char in \"-. \" for char in l1):\n",
        "                return l1\n",
        "        \n",
        "        # Сборка из компонентов (Классический / Fallback)\n",
        "        parts = []\n",
        "        if street or house:\n",
        "            if street:\n",
        "                if not any(pref in street.lower() for pref in [\"ул.\", \"пр.\", \"пер.\", \"б-р\"]):\n",
        "                    parts.append(f\"ул. {street}\")\n",
        "                else:\n",
        "                    parts.append(street)\n",
        "            \n",
        "            if house and house != \"0\":\n",
        "                parts.append(f\"д. {house}\")\n",
        "            \n",
        "            if flat: parts.append(f\"кв. {flat}\")\n",
        "            if entrance: parts.append(f\"под. {entrance}\")\n",
        "            if floor: parts.append(f\"эт. {floor}\")\n",
        "            \n",
        "            addr_str = \", \".join(parts)\n",
        "            if final_city and final_city.lower() not in addr_str.lower():\n",
        "                return f\"г. {final_city}, {addr_str}\"\n",
        "            return addr_str\n",
        "\n",
        "        # Если компонентов нет, пробуем line1 как последний шанс\n",
        "        l1 = clean(addr_obj.get(\"line1\") or addr_obj.get(\"addressString\"))\n",
        "        if l1 and len(l1) > 2 and not all(char in \"-. \" for char in l1):\n",
        "            if final_city and final_city.lower() not in l1.lower():\n",
        "                return f\"г. {final_city}, {l1}\"\n",
        "            return l1\n",
        "\n",
        "        return f\"г. {final_city}\"\n"
    ]
    lines[s1:e1+1] = new_format
    print("format_address updated")
else:
    print(f"format_address not found (s1={s1}, e1={e1})")

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
