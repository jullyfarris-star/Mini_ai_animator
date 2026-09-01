import json
import os
import math
from PIL import Image, ImageDraw

def create_transparent_mock_image(path):
    """Створює тестового персонажа, якщо ви ще не поклали власне фото original.png"""
    print("🎨 original.png не знайдено. Створюємо шаблон персонажа на прозорому тлі...")
    img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((360, 100, 440, 180), fill=(230, 230, 250, 255)) # Head
    draw.rectangle((340, 210, 460, 360), fill=(0, 150, 255, 255)) # Body
    draw.rectangle((240, 230, 310, 270), fill=(255, 200, 0, 255)) # Arm Left
    draw.rectangle((490, 230, 560, 270), fill=(255, 200, 0, 255)) # Arm Right
    img.save(path)

def find_connected_components(img):
    """Розумний сканер прозорості: шукає окремі деталі на фото"""
    width, height = img.size
    pixels = img.load()
    visited = set()
    components = []

    for x in range(0, width, 8):
        for y in range(0, height, 8):
            if (x, y) in visited: continue
            if pixels[x, y][3] > 50: # Перевірка альфа-каналу (непрозорості)
                x_min, y_min = x, y
                x_max, y_max = x, y
                queue = [(x, y)]
                visited.add((x, y))
                while queue:
                    cx, cy = queue.pop(0)
                    x_min, y_min = min(x_min, cx), min(y_min, cy)
                    x_max, y_max = max(x_max, cx), max(y_max, cy)
                    for nx, ny in [(cx+20, cy), (cx-20, cy), (cx, cy+20), (cx, cy-20)]:
                        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                            if pixels[nx, ny][3] > 50:
                                visited.add((nx, ny))
                                queue.append((nx, ny))
                if (x_max - x_min) > 15 and (y_max - y_min) > 15:
                    components.append((x_min, y_min, x_max, y_max))
    return components

def generate_mesh_data(w, h):
    """Створює еластичну сітку Mesh (3х3 точки) для деформації"""
    vertices = [
        -w//2, -h//2,   0, -h//2,   w//2, -h//2,
        -w//2,  0,      0,  0,      w//2,  0,
        -w//2,  h//2,   0,  h//2,   w//2,  h//2
    ]
    triangles = [0,1,3, 1,4,3, 1,2,4, 2,5,4, 3,4,6, 4,7,6, 4,5,7, 5,8,7]
    uvs = [0.0,0.0, 0.5,0.0, 1.0,0.0, 0.0,0.5, 0.5,0.5, 1.0,0.5, 0.0,1.0, 0.5,1.0, 1.0,1.0]
    return vertices, triangles, uvs

def process_and_slice_image_mesh():
    base_dir = os.path.join("data", "animations", "scenario_5")
    textures_dir = os.path.join(base_dir, "textures")
    os.makedirs(textures_dir, exist_ok=True)
    
    orig_path = os.path.join(base_dir, "original.png")
    if not os.path.exists(orig_path):
        create_transparent_mock_image(orig_path)
        
    orig_img = Image.open(orig_path).convert("RGBA")
    boxes = sorted(find_connected_components(orig_img), key=lambda b: (b[0], b[1]))
    
    part_names = ["head", "body", "arm_left", "arm_right"]
    slice_map = {}
    
    for i, box in enumerate(boxes):
        name = part_names[i] if i < len(part_names) else f"extra_{i}"
        slice_map[name] = box
        cropped = orig_img.crop(box)
        cropped.save(os.path.join(textures_dir, f"{name}.png"), "PNG")

    spine_data = {
        "skeleton": {"hash": "aelis_mesh_v5", "spine": "3.8.99", "width": 800, "height": 600},
        "bones": [{"name": "root", "x": 400, "y": 100}],
        "slots": [],
        "skins": {"default": {}},
        "animations": {"scenario_5_idle_action": {"attachments": {}}}
    }
    
    for name, box in slice_map.items():
        x_center, y_center = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        spine_x, spine_y = x_center - 400, 600 - y_center - 100
        parent = "root" if name == "body" else "body"
        
        spine_data["bones"].append({
            "name": name,
            "parent": parent if name != "body" else "root",
            "x": spine_x if name == "body" else spine_x - (spine_data["bones"][1]["x"] if len(spine_data["bones"]) > 1 else 0),
            "y": spine_y if name == "body" else spine_y - (spine_data["bones"][1]["y"] if len(spine_data["bones"]) > 1 else 0)
        })
        spine_data["slots"].append({"name": name, "bone": name, "attachment": name})
        
        w, h = box[2] - box[0], box[3] - box[1]
        v, t, u = generate_mesh_data(w, h)
        
        if name not in spine_data["skins"]["default"]:
            spine_data["skins"]["default"][name] = {}
            
        spine_data["skins"]["default"][name][name] = {
            "type": "mesh", "width": w, "height": h, "vertices": v, "triangles": t, "uvs": u
        }

    # Математика хвиль для Сценарію №5
    total_frames = 60
    for name in slice_map.keys():
        spine_data["animations"]["scenario_5_idle_action"]["attachments"][name] = {name: {"mesh": []}}
        for frame in range(total_frames):
            time_sec = frame / 30.0
            wave = math.sin(time_sec * math.pi * 2)
            offset_vertices = [0.0] * 18 
            
            if name == "body":
                offset_vertices[6] = offset_vertices[8] = offset_vertices[10] = round(12 * wave, 2)
            elif "arm" in name:
                mult = 1 if "right" in name else -1
                offset_vertices[12] = offset_vertices[14] = offset_vertices[16] = round(20 * wave * mult, 2)
                
            spine_data["animations"]["scenario_5_idle_action"]["attachments"][name][name]["mesh"].append({
                "time": round(time_sec, 4), "vertices": offset_vertices
            })
            
    json_path = os.path.join(base_dir, "skeleton.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spine_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Скелет та Меш-сітку успішно згенеровано у: {json_path}")

if __name__ == "__main__":
    process_and_slice_image_mesh()
