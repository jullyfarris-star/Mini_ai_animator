import json
import os
import math

def setup_spine_pipeline():
    # Шлях до папки Сценарію 5
    base_dir = os.path.join("data", "animations", "scenario_5")
    textures_dir = os.path.join(base_dir, "textures")
    os.makedirs(textures_dir, exist_ok=True)
    
    print("✂️ [Aelis Pipeline] Ініціалізація нарізання частин та збирання скелета...")
    
    # 1. Емуляція збереження вирізаних деталей (атласу)
    # У реальному кейсі тут Pillow (PIL) вирізає координати по масці
    parts = ["root", "body", "head", "arm_left", "arm_right"]
    for part in parts:
        part_path = os.path.join(textures_dir, f"{part}.png")
        if not os.path.exists(part_path):
            with open(part_path, "w") as f:
                f.write("PNG_MOCK_DATA") # Заглушка для рушія
                
    # 2. Створення структури Spine-сумісного JSON (Кістки, Слоти, Анімація)
    spine_data = {
        "skeleton": {
            "hash": "aelis_scen5_v1",
            "spine": "3.8.99", # Стандартна версія для максимального імпорту в Unity/Godot
            "width": 800,
            "height": 600
        },
        "bones": [
            {"name": "root", "x": 0, "y": 0},
            {"name": "body", "parent": "root", "x": 0, "y": 100},
            {"name": "head", "parent": "body", "x": 0, "y": 120},
            {"name": "arm_left", "parent": "body", "x": -60, "y": 80},
            {"name": "arm_right", "parent": "body", "x": 60, "y": 80}
        ],
        "slots": [
            {"name": "body", "bone": "body", "attachment": "body"},
            {"name": "head", "bone": "head", "attachment": "head"},
            {"name": "arm_left", "bone": "arm_left", "attachment": "arm_left"},
            {"name": "arm_right", "bone": "arm_right", "attachment": "arm_right"}
        ],
        "animations": {
            "scenario_5_idle_action": {
                "bones": {
                    "body": {
                        "translate": [],
                        "scale": []
                    },
                    "head": {
                        "rotate": []
                    },
                    "arm_left": {
                        "rotate": []
                    }
                }
            }
        }
    }
    
    # 3. Генерація математики для Сценарію 5 (Циклічна анімація, 60 кадрів, 30 FPS)
    # Сценарій 5: Дихання тіла, похитування голови, циклічний рух руки
    total_frames = 60
    for frame in range(total_frames):
        time_sec = frame / 30.0
        angle_wave = math.sin(time_sec * math.pi * 2) # Період 1 сек
        
        # Тіло (Дихання: легке стискання по Y, розширення по X)
        scale_x = 1.0 + 0.02 * angle_wave
        scale_y = 1.0 - 0.02 * angle_wave
        spine_data["animations"]["scenario_5_idle_action"]["bones"]["body"]["scale"].append({
            "time": round(time_sec, 4), "x": round(scale_x, 3), "y": round(scale_y, 3)
        })
        
        # Голова (Погойдування)
        head_rot = 5 * math.cos(time_sec * math.pi)
        spine_data["animations"]["scenario_5_idle_action"]["bones"]["head"]["rotate"].append({
            "time": round(time_sec, 4), "angle": round(head_rot, 2)
        })
        
        # Ліва рука (Махання/Рух за сценарієм)
        arm_rot = 25 * angle_wave
        spine_data["animations"]["scenario_5_idle_action"]["bones"]["arm_left"]["rotate"].append({
            "time": round(time_sec, 4), "angle": round(arm_rot, 2)
        })
        
    # Запис у файл
    json_path = os.path.join(base_dir, "skeleton.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spine_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ [Aelis Pipeline] Файли згенеровано! Скелет та анімація збережені в: {json_path}")

if __name__ == "__main__":
    setup_spine_pipeline()
