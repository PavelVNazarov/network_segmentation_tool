# tests/test_risk_analyzer.py
import unittest
from risk_analyzer import analyze_risks

class TestRiskAnalyzerEdgeCases(unittest.TestCase):

    def test_risk_analyzer_empty_inputs(self):
        risks = analyze_risks([], [], [], {})
        # Должен вернуть "не содержит рисков", так как нет данных для анализа
        self.assertEqual(risks, ["Модель не содержит явных рисков."])

    def test_risk_analyzer_custom_service_ignored(self):
        global_rules = [("R1", "HR", "IT", "Custom")]
        # Укажем оборудование, чтобы избежать предупреждений о пустых сегментах
        equipment = {"HR": {"Workstation": 1}, "IT": {"Server": 1}}
        risks = analyze_risks(["HR", "IT"], global_rules, [], equipment)
        # Custom не в списке опасных — рисков быть не должно
        self.assertEqual(risks, ["Модель не содержит явных рисков."])

    def test_risk_analyzer_all_segments_empty_equipment(self):
        risks = analyze_risks(["A", "B"], [], [], {"A": {}, "B": {}})
        self.assertTrue(any("Сегмент 'A' не содержит оборудования" in r for r in risks))
        self.assertTrue(any("Сегмент 'B' не содержит оборудования" in r for r in risks))

    def test_risk_analyzer_guest_case_insensitive(self):
        # Проверим, что "GUEST", "guest", "Guest" распознаются
        for guest_name in ["GUEST", "guest", "Guest"]:
            risks = analyze_risks(
                [guest_name, "IT"],
                [("R1", guest_name, "IT", "HTTPS")],
                [],
                {guest_name: {}, "IT": {}}
            )
            self.assertTrue(
                any("ненадёжного сегмента" in r for r in risks),
                f"Не распознан сегмент '{guest_name}' как Guest"
            )


if __name__ == '__main__':
    unittest.main()

