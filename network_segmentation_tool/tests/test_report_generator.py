# tests/test_report_generator.py
import unittest
from report_generator import generate_report

class TestReportGeneratorEdgeCases(unittest.TestCase):

    def test_generate_report_empty_everything(self):
        report = generate_report([], {}, [], [], {}, validation_errors=[])
        self.assertIn("Модель прошла валидацию успешно", report)
        self.assertIn("Отсутствуют", report)
        self.assertIn("Не заданы", report)
        self.assertIn("Не указано", report)

    def test_generate_report_custom_service(self):
        global_rules = [("R1", "HR", "IT", "Custom")]
        user_rules = [("HR", "Иван", "Админ", "IT", "Custom")]
        report = generate_report(
            ["HR", "IT"], {"HR": "1.1.1.0/24", "IT": "1.1.2.0/24"},
            global_rules, user_rules, {}, []
        )
        self.assertIn("Custom", report)

    def test_generate_report_no_subnets(self):
        report = generate_report(
            ["HR", "IT"], {"HR": "", "IT": ""}, [], [], {}, []
        )
        self.assertIn("не задано", report)

    def test_generate_report_with_errors_only(self):
        errors = ["Ошибка 1", "Ошибка 2"]
        report = generate_report([], {}, [], [], {}, validation_errors=errors)
        self.assertIn("ОБНАРУЖЕНЫ ОШИБКИ", report)
        self.assertIn("Ошибка 1", report)
        self.assertIn("Ошибка 2", report)


if __name__ == '__main__':
    unittest.main()

