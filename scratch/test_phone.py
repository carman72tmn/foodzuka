import re

def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r'\D', '', str(phone))
    if not digits:
        return ""
    if len(digits) == 10:
        digits = "7" + digits
    elif len(digits) == 11:
        if digits.startswith("8"):
            digits = "7" + digits[1:]
    return f"+{digits}"

print(f"Normal: {normalize_phone('+79962108356')}")
print(f"Double: {normalize_phone('++79962108356')}")
print(f"8 start: {normalize_phone('89962108356')}")
print(f"No plus: {normalize_phone('79962108356')}")
