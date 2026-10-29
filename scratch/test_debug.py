import re

text = "Привет! Мой заказ № RU-555."
parser_mask = "RU-***"

def check_mask(order_id: str, mask: str) -> bool:
    parts = []
    for char in mask.strip():
        if char == '*':
            parts.append('.')
        else:
            parts.append(re.escape(char))
    pattern = "^" + "".join(parts) + "$"
    print("Mask Pattern:", pattern)
    print("Checking Order ID:", order_id)
    return bool(re.match(pattern, order_id))

match = re.search(r'(?:заказ|заказа)(?:\s*(?:№|#|номер|номера))?\s*(\S+)', text, re.IGNORECASE)
if match:
    candidate = match.group(1)
    print("Match found candidate:", candidate)
    candidate = candidate.rstrip('.,!?;:)')
    print("Cleaned candidate:", candidate)
    res = check_mask(candidate, parser_mask)
    print("Matches mask?", res)
else:
    print("No match found at all by regex")
