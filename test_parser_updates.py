import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.services.vk_service import extract_order_id_from_text, is_ignored_vk_id

def test():
    print("=== TESTING PARSER UPDATES ===")
    
    # 1. Тест строгого совпадения по фразе
    phrase = "здравствуйте! Ваш заказ {order_id} принят"
    
    # Полное совпадение
    msg1 = "здравствуйте! Ваш заказ 12345 принят"
    res1 = extract_order_id_from_text(msg1, True, phrase)
    print(f"Full match test: '{msg1}' -> expected '12345', got '{res1}'")
    assert res1 == "12345"
    
    # Подстрочное совпадение (лишний текст в начале/конце)
    msg2 = "Привет, здравствуйте! Ваш заказ 12345 принят"
    res2 = extract_order_id_from_text(msg2, True, phrase)
    print(f"Substring match test (prefix): '{msg2}' -> expected '12345', got '{res2}'")
    assert res2 == "12345"
    
    msg3 = "здравствуйте! Ваш заказ 12345 принят. Ждем вас!"
    res3 = extract_order_id_from_text(msg3, True, phrase)
    print(f"Substring match test (suffix): '{msg3}' -> expected '12345', got '{res3}'")
    assert res3 == "12345"
    
    # Лишние пробелы в начале/конце
    msg4 = "  здравствуйте! Ваш заказ 12345 принят \n"
    res4 = extract_order_id_from_text(msg4, True, phrase)
    print(f"Strip spaces test: '{msg4.strip()}' -> expected '12345', got '{res4}'")
    assert res4 == "12345"
    
    # 2. Тест игнорируемых ID
    ignored_str = " 12345, 67890 , 11111"
    print(f"Ignore list: '{ignored_str}'")
    
    test_id1 = 12345
    res_ign1 = is_ignored_vk_id(test_id1, ignored_str)
    print(f"Check {test_id1} -> expected True, got {res_ign1}")
    assert res_ign1 is True
    
    test_id2 = 99999
    res_ign2 = is_ignored_vk_id(test_id2, ignored_str)
    print(f"Check {test_id2} -> expected False, got {res_ign2}")
    assert res_ign2 is False
    
    test_id3 = 67890
    res_ign3 = is_ignored_vk_id(test_id3, ignored_str)
    print(f"Check {test_id3} -> expected True, got {res_ign3}")
    assert res_ign3 is True

    print("=== ALL TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test()
