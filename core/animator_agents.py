import os
import json
import shutil

class AnimationFileManager:
    """Агент 6: Відповідає за збереження сировини, логів, папок та експорт коду"""
    def __init__(self, project_name="Aelis_Project"):
        self.project_name = project_name
        self.base_dir = f"data/animator_{project_name}"
        self.parts_dir = os.path.join(self.base_dir, "cut_parts")
        
        # Автоматично створюємо правильну структуру репозиторію
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.parts_dir, exist_ok=True)
        
    def save_original_source(self, source_path):
        """Зберігає недоторканий оригінал («сировину»)"""
        destination = os.path.join(self.base_dir, "original_source.png")
        shutil.copy(source_path, destination)
        print(f"[Агент 2]: Сировину зафіксовано за адресою: {destination}")
        return destination

    def create_timeline_config(self, text_script):
        """Агент 5 (Валідатор): Перекладає твій текстовий сценарій з iPhone у JSON-конфіг"""
        # Тимчасова базова структура, яку ми наповнюватимемо за твоїм сценарієм
        config = {
            "project": self.project_name,
            "status": "waiting_validation",
            "raw_script": text_script,
            "detected_layers": ["hair_front", "scene_background", "eyes_blink"],
            "timeline": []
        }
        
        config_path = os.path.join(self.base_dir, "timeline_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        print(f"[Агент Валідації]: План-звіт згенеровано для iPhone 11!")
        return config_path
