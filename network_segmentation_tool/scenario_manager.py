# scenario_manager.py
import json
import os
from datetime import datetime

SCENARIOS_DIR = "scenarios"

class ScenarioManager:
    def __init__(self):
        os.makedirs(SCENARIOS_DIR, exist_ok=True)

    def save_scenario(self, scenario_data, name):
        """Сохраняет сценарий в JSON."""
        filename = os.path.join(SCENARIOS_DIR, f"{name}.json")
        scenario_data['saved_at'] = datetime.now().isoformat()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scenario_data, f, ensure_ascii=False, indent=2)
        return filename

    def load_scenario(self, name):
        """Загружает сценарий из JSON."""
        filename = os.path.join(SCENARIOS_DIR, f"{name}.json")
        if not os.path.exists(filename):
            return None
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_scenarios(self):
        """Возвращает список доступных сценариев."""
        files = [f for f in os.listdir(SCENARIOS_DIR) if f.endswith('.json')]
        return [f[:-5] for f in files]