import sys
import os

# Добавляем путь к backend, чтобы импортировать vk_service
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.vk_service import extract_order_id_from_text

def run_tests():
    # Шаблон фразы: "Ваш заказ {order_id} принят"
    phrase = "Ваш заказ {order_id} принят"
    
    tests = [
        # 1. Тесты без маски (или с маской "*")
        {
            "text": "Ваш заказ 12345 принят",
            "mask": "*",
            "expected": "12345",
            "desc": "Без маски (любое число)"
        },
        {
            "text": "Ваш заказ RU-999 принят",
            "mask": "",
            "expected": "RU-999",
            "desc": "Без маски (любой буквенно-цифровой)"
        },
        # 2. Маска с фиксированной длиной и символами
        {
            "text": "Ваш заказ RU-123 принят",
            "mask": "RU-***",
            "expected": "RU-123",
            "desc": "Маска RU-***, совпадение"
        },
        {
            "text": "Ваш заказ RU-12 принят",
            "mask": "RU-***",
            "expected": None,
            "desc": "Маска RU-***, слишком короткий"
        },
        {
            "text": "Ваш заказ US-123 принят",
            "mask": "RU-***",
            "expected": None,
            "desc": "Маска RU-***, префикс не совпадает"
        },
        # 3. Маска со случайными символами (буквы, цифры)
        {
            "text": "Ваш заказ ZK-987-A принят",
            "mask": "ZK-***-*",
            "expected": "ZK-987-A",
            "desc": "Сложная комбинированная маска ZK-***-*, совпадение"
        },
        {
            "text": "Ваш заказ ZK-987-AB принят",
            "mask": "ZK-***-*",
            "expected": None,
            "desc": "Сложная комбинированная маска ZK-***-*, лишние символы"
        },
        # 4. Фолбэк поиск (если нет точной фразы, но в тексте есть ключевые слова заказ/№/номер)
        {
            "text": "Привет! Мой заказ № RU-555.",
            "mask": "RU-***",
            "expected": "RU-555",
            "desc": "Фолбэк поиск с маской, совпадение"
        },
        {
            "text": "Привет! Мой заказ № 12345.",
            "mask": "RU-***",
            "expected": None,
            "desc": "Фолбэк поиск с маской, не совпадает с маской"
        },
        {
            "text": "Привет! Мой заказ № 12345.",
            "mask": None,
            "expected": "12345",
            "desc": "Фолбэк поиск без маски (ищет цифры), совпадение"
        }
    ]
    
    passed = 0
    for i, t in enumerate(tests):
        res = extract_order_id_from_text(t["text"], parser_enabled=True, parser_phrase=phrase, parser_mask=t["mask"])
        if res == t["expected"]:
            print(f"Test {i+1} PASSED: {t['desc']} -> Получено: {res}")
            passed += 1
        else:
            print(f"Test {i+1} FAILED: {t['desc']} -> Ожидалось: {t['expected']}, Получено: {res}")
            
    print(f"\nИтог: {passed} / {len(tests)} тестов пройдено.")

if __name__ == "__main__":
    run_tests()
