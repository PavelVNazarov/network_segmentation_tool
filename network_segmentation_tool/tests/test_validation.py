# tests/test_validation.py
import unittest
from validation import validate_subnets, validate_rules, validate_user_rules

class TestValidationEdgeCases(unittest.TestCase):

    # --- Подсети ---
    def test_validate_subnets_empty(self):
        errors = validate_subnets({})
        self.assertEqual(errors, [])

    def test_validate_subnets_missing_cidr(self):
        subnets = {"HR": "", "IT": "192.168.2.0/24"}
        errors = validate_subnets(subnets)
        # Пустая строка не вызывает ошибку валидации CIDR (пропускается)
        self.assertEqual(errors, [])

    def test_validate_subnets_custom_overlap_with_valid(self):
        # Пересечение: /24 и /25 внутри него
        subnets = {"A": "10.0.0.0/24", "B": "10.0.0.0/25"}
        errors = validate_subnets(subnets)
        self.assertIn("Пересечение подсетей", errors[0])

    # --- Глобальные правила ---
    def test_validate_rules_empty(self):
        errors = validate_rules([], ["HR", "IT"])
        self.assertEqual(errors, [])

    def test_validate_rules_custom_service(self):
        rules = [("R1", "HR", "IT", "Custom")]
        errors = validate_rules(rules, ["HR", "IT"])
        self.assertEqual(errors, [])  # Custom разрешён

    def test_validate_rules_missing_segment(self):
        rules = [("R1", "HR", "NonExistent", "SSH")]
        errors = validate_rules(rules, ["HR", "IT"])
        self.assertIn("Неизвестный сегмент", errors[0])

    def test_validate_rules_self_loop_allowed(self):
        rules = [("R1", "HR", "HR", "SSH")]
        errors = validate_rules(rules, ["HR", "IT"])
        self.assertEqual(errors, [])  # Самодоступ разрешён

    # --- Пользовательские правила ---
    def test_validate_user_rules_empty(self):
        errors = validate_user_rules([], ["HR", "IT"])
        self.assertEqual(errors, [])

    def test_validate_user_rules_custom_service(self):
        user_rules = [("HR", "Иван", "Админ", "IT", "Custom")]
        errors = validate_user_rules(user_rules, ["HR", "IT"])
        self.assertEqual(errors, [])

    def test_validate_user_rules_missing_source_segment(self):
        user_rules = [("NonExistent", "Иван", "Админ", "IT", "SSH")]
        errors = validate_user_rules(user_rules, ["HR", "IT"])
        self.assertIn("сегмент источника", errors[0])

    # --- Дубликаты правил ---
    def test_validate_rules_duplicate_with_custom(self):
        rules = [
            ("R1", "HR", "IT", "Custom"),
            ("R2", "HR", "IT", "Custom")
        ]
        errors = validate_rules(rules, ["HR", "IT"])
        self.assertIn("Дублирующее правило", errors[0])

    def test_validate_user_rules_duplicate_different_positions(self):
        # Один пользователь, одинаковые доступы — дубликат
        user_rules = [
            ("HR", "Иван", "Админ", "IT", "SSH"),
            ("HR", "Иван", "Админ", "IT", "SSH")
        ]
        errors = validate_user_rules(user_rules, ["HR", "IT"])
        self.assertIn("Дублирующее правило для пользователя", errors[0])

    def test_validate_user_rules_same_fio_different_segments(self):
        # Разные сегменты — не дубликат
        user_rules = [
            ("HR", "Иван", "Админ", "IT", "SSH"),
            ("Finance", "Иван", "Админ", "IT", "SSH")
        ]
        errors = validate_user_rules(user_rules, ["HR", "Finance", "IT"])
        self.assertEqual(errors, [])  # Не дубликат


class TestSegmentNameValidationInGUI(unittest.TestCase):
    """
    Хотя основная валидация имён сегментов происходит в main.py,
    логика проверки дубликатов и формата может быть протестирована отдельно.
    """

    def test_segment_name_duplicates(self):
        # Эмуляция данных из GUI
        segment_rows = [
            (None, MockEntry("HR"), MockEntry("192.168.1.0/24")),
            (None, MockEntry("HR"), MockEntry("192.168.2.0/24")),
        ]
        segments = []
        errors = []
        seen_names = set()
        for _, name_ent, _ in segment_rows:
            name = name_ent.get().strip()
            if not name:
                continue
            if not name.replace('_', '').replace('-', '').isalnum():
                errors.append(f"Недопустимое имя сегмента: '{name}'")
            elif name in seen_names:
                errors.append(f"Дублирование сегмента: '{name}'")
            else:
                seen_names.add(name)
                segments.append(name)

        self.assertIn("Дублирование сегмента: 'HR'", errors)

    def test_invalid_segment_name(self):
        name = "HR@123"
        self.assertFalse(name.replace('_', '').replace('-', '').isalnum())


# Вспомогательный класс для эмуляции Entry
class MockEntry:
    def __init__(self, text):
        self.text = text
    def get(self):
        return self.text


if __name__ == '__main__':
    unittest.main()

