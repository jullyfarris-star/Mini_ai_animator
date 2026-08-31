import json
import os
import math
from PIL import Image, ImageDraw

def create_mock_original_image(path):
    """Створює тимчасове оригінальне фото, якщо користувач ще не поклав своє"""
    print("🎨 [Aelis] original.png не знайдено. Створюємо тестовий шаблон для нарізки...")
    # Створюємо базове прозоре полотно 800х600
    img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Малюємо умовного персонажа, якого будемо різати:
    draw.ellipse([350, 150, 450, 250], fill=(230, 230, 250, 255)) # Голова (світла)
    draw.rectangle([330, 250, 470, 450], fill=(0, 150, 255, 255)) # Тіло (синє)
    draw.rectangle([250, 270, 330, 310], fill=(255, 200, 0, 255)) # Ліва рука (жовта)
    draw.rectangle([470, 270, 550, 310], fill=(255, 200, 0, 255)) # Права рука (жовта)
    
    img.save(path)

def process_and_slice_image():
    base_dir = os.path.join("data", "animations", "scenario_5")
    textures_dir = os.path.join(base_dir, "textures")
    os.makedirs(textures_dir, exist_ok=True)
    
    orig_path = os.path.join(base_dir, "original.png")
    if not os.path.exists(orig_path):
        create_mock_original_image(orig_path)
        
    # Відкриваємо оригінальне фото
    orig_img = Image.open(orig_path).convert("RGBA")
    
    # ✂️ Мапа координат для вирізання деталей (Задаємо рамки: x_min, y_min, x_max, y_max)
    # Коли ви покладете своє фото, просто підправте ці цифри під ваші деталі!
    slice_map = {
        "head": (350, 150, 450, 250),
        "body": (330, 250, 470, 450),
        "arm_left": (250, 270, 330, 310),
        "arm_right": (470, 270, 550, 310)
    }
    
    print("✂️ [Aelis] Pillow нарізає оригінальне фото на окремі шари текстур...")
    for part_name, box in slice_map.items():
        # Вирізаємо частину з оригіналу
        cropped_part = orig_img.crop(box)
        
        # Зберігаємо як окремий файл png з прозорістю
        part_path = os.path.join(textures_dir, f"{part_name}.png")
        cropped_part.save(part_path, "PNG")
        print(f"   └─📁 Збережено деталь: {part_path} (Розмір: {cropped_part.size})")

    # 📐 Збирання структури скелету Spine JSON
    spine_data = {
        "skeleton": {
            "hash": "aelis_scen5_v1",
            "spine": "3.8.99",
            "width": 800,
            "height": 600
        },
        "bones": [
            {"name": "root", "x": 400, "y": 100}, # Центруємо відносно екрану 800х600
            {"name": "body", "parent": "root", "x": 0, "y": 0},
            {"name": "head", "parent": "body", "x": 0, "y": 150},
            {"name": "arm_left", "parent": "body", "x": -80, "y": 100},
            {"name": "arm_right", "parent": "body", "x": 80, "y": 100}
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
                    "body": {"scale": []},
                    "head": {"rotate": []},
                    "arm_left": {"rotate": []},
                    "arm_right": {"rotate": []}
                }
            }
        }
    }
    
    # 🎬 Генерація математики анімації для Сценарію 5 (60 кадрів, 30 FPS)
    total_frames = 60
    for frame in range(total_frames):
        time_sec = frame / 30.0
        wave = math.sin(time_sec * math.pi * 2)
        
        # Тіло (Ефект дихання)
        spine_data["animations"]["scenario_5_idle_action"]["bones"]["body"]["scale"].append({
            "time": round(time_sec, 4), "x": round(1.0 + 0.03 * wave, 3), "y": round(1.0 - 0.02 * wave, 3)
        })
        # Голова (Легке похитування)
        spine_data["animations"]["scenario_5_idle_action"]["bones"]["head"]["rotate"].append({
            "time": round(time_sec, 4), "angle": round(4 * math.cos(time_sec * math.pi), 2)
        })
        # Ліва рука (Циклічне махання вгору-вниз)
        spine_data["animations"]["scenario_5_idle_action"]["bones"]["arm_left"]["rotate"].append({
            "time": round(time_sec, 4), "angle": round(30 * wave, 2)
        })
        # Права рука (Протифаза до лівої)
        spine_data["animations"]["scenario_5_idle_action"]["bones"]["arm_right"]["rotate"].append({
            "time": round(time_sec, 4), "angle": round(-15 * wave, 2)
        })
        
    json_path = os.path.join(base_dir, "skeleton.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spine_data, f, indent=4, ensure_ascii=False)
        
    print(f"📦 [Aelis] Кросплатформний Spine-пакет успішно згенеровано у: {json_path}")

if __name__ == "__main__":
    process_and_slice_image()
