import os
import json
import pygame
import sys
import math

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎭 Aelis Cross-Platform Spine Runtime")
clock = pygame.time.Clock()

def load_spine_animation():
    path = os.path.join("data", "animations", "scenario_5", "skeleton.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

data = load_spine_animation()
if not data:
    print("❌ Помилка: Спочатку запустіть core/spine_pipeline.py для генерації JSON!")
    sys.exit()

bones = {b["name"]: b for b in data["bones"]}
anim_timeline = data["animations"]["scenario_5_idle_action"]["bones"]

frame_idx = 0
total_frames = 60
font = pygame.font.SysFont("Arial", 14)

while True:
    screen.fill((35, 35, 40))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
    # Читаємо ключі трансформації з JSON для поточного кадру
    body_scale = anim_timeline["body"]["scale"][frame_idx]
    head_rot = anim_timeline["head"]["rotate"][frame_idx]["angle"]
    arm_rot = anim_timeline["arm_left"]["rotate"][frame_idx]["angle"]
    
    # Розрахунок позицій кісток у просторі (Ієрархія склепу)
    center_x, center_y = WIDTH // 2, HEIGHT // 2 + 50
    
    # 1. Корінь (Root)
    root_pos = (center_x, center_y)
    
    # 2. Тіло (Батько для голови й рук)
    b_scale_x, b_scale_y = body_scale["x"], body_scale["y"]
    body_pos = (center_x + bones["body"]["x"], center_y - bones["body"]["y"])
    
    # 3. Голова (Враховує позицію тіла + обертання з JSON)
    h_rad = math.radians(head_rot)
    head_pos = (body_pos[0] + bones["head"]["x"], body_pos[1] - bones["head"]["y"] * b_scale_y)
    
    # 4. Ліва рука
    a_rad = math.radians(arm_rot)
    arm_pos = (body_pos[0] + bones["arm_left"]["x"] * b_scale_x, body_pos[1] - bones["arm_left"]["y"])
    arm_end = (arm_pos[0] + 80 * math.sin(a_rad), arm_pos[1] + 80 * math.cos(a_rad))

    # --- Візуалізація Скелету та Вирізаних Деталей (Склепів) ---
    # Малюємо кістки
    pygame.draw.line(screen, (0, 255, 255), root_pos, body_pos, 5) # Спина
    pygame.draw.line(screen, (255, 0, 255), body_pos, head_pos, 4) # Шия
    pygame.draw.line(screen, (255, 255, 0), body_pos, arm_pos, 4)  # Плече
    pygame.draw.line(screen, (255, 100, 0), arm_pos, arm_end, 6)  # Рука, що рухається
    
    # Емуляція відмальовки спрайтів деталей (текстур)
    pygame.draw.circle(screen, (0, 180, 255), (int(body_pos[0]), int(body_pos[1])), int(40 * b_scale_x)) # Тіло
    pygame.draw.circle(screen, (230, 230, 250), (int(head_pos[0]), int(head_pos[1])), 30) # Голова
    pygame.draw.circle(screen, (255, 50, 50), (int(arm_end[0]), int(arm_end[1])), 10) # Кисть руки
    
    # Виведення логу таймлайну JSON
    txt_info = font.render(f"Spine JSON Runtime: Frame {frame_idx}/60 | Active Bone: arm_left rot={arm_rot}°", True, (200, 200, 200))
    txt_engine = font.render("Cross-platform Export: Unity / Godot / PixiJS ready (Spine 3.8 structure)", True, (100, 200, 100))
    screen.blit(txt_info, (20, 20))
    screen.blit(txt_engine, (20, 45))
    
    frame_idx = (frame_idx + 1) % total_frames
    pygame.display.flip()
    clock.tick(30)
