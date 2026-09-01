import os
import json
import pygame
import sys
import math

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎭 Aelis Real-Texture Spine Player")
clock = pygame.time.Clock()

base_path = os.path.join("data", "animations", "scenario_5")
json_path = os.path.join(base_path, "skeleton.json")

if not os.path.exists(json_path):
    print("❌ Помилка: Спочатку запустіть core/spine_pipeline.py!")
    sys.exit()

with open(json_path, "r", encoding="utf-8") as f:
    spine_data = json.load(f)

# Завантажуємо реальні текстури, які вирізав модуль Pillow
textures = {}
parts = ["body", "head", "arm_left", "arm_right"]
for part in parts:
    tex_path = os.path.join(base_path, "textures", f"{part}.png")
    if os.path.exists(tex_path):
        textures[part] = pygame.image.load(tex_path).convert_alpha()

bones = {b["name"]: b for b in spine_data["bones"]}
anim_timeline = spine_data["animations"]["scenario_5_idle_action"]["bones"]

frame_idx = 0
total_frames = 60

def draw_rotated_sprite(surface, image, center_pos, angle, scale=(1.0, 1.0)):
    """Допоміжний метод для обертання та масштабування нарізаних шарів текстур"""
    w, h = image.get_size()
    scaled_img = pygame.transform.smoothscale(image, (int(w * scale[0]), int(h * scale[1])))
    rotated_img = pygame.transform.rotate(scaled_img, angle)
    new_rect = rotated_img.get_rect(center=center_pos)
    surface.blit(rotated_img, new_rect.topleft)

while True:
    screen.fill((40, 40, 45))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
    # Отримуємо трансформації з таймлайну
    b_scale = anim_timeline["body"]["scale"][frame_idx]
    h_rot = anim_timeline["head"]["rotate"][frame_idx]["angle"]
    al_rot = anim_timeline["arm_left"]["rotate"][frame_idx]["angle"]
    ar_rot = anim_timeline["arm_right"]["rotate"][frame_idx]["angle"]
    
    # Розрахунок позицій склепів на екрані (Базовий центр з root кістки)
    rx, ry = bones["root"]["x"], HEIGHT - bones["root"]["y"]
    
    # 1. Тіло
    body_pos = (rx + bones["body"]["x"], ry - bones["body"]["y"])
    
    # 2. Голова (відносно тіла)
    head_pos = (body_pos[0] + bones["head"]["x"], body_pos[1] - bones["head"]["y"] * b_scale["y"])
    
    # 3. Руки (відносно тіла)
    al_pos = (body_pos[0] + bones["arm_left"]["x"] * b_scale["x"], body_pos[1] - bones["arm_left"]["y"])
    ar_pos = (body_pos[0] + bones["arm_right"]["x"] * b_scale["x"], body_pos[1] - bones["arm_right"]["y"])

    # Відмальовуємо шари (у порядку черговості верств / Слотів Spine)
    if "arm_left" in textures:
        draw_rotated_sprite(screen, textures["arm_left"], al_pos, al_rot)
    if "arm_right" in textures:
        draw_rotated_sprite(screen, textures["arm_right"], ar_pos, ar_rot)
    if "body" in textures:
        draw_rotated_sprite(screen, textures["body"], body_pos, 0, scale=(b_scale["x"], b_scale["y"]))
    if "head" in textures:
        draw_rotated_sprite(screen, textures["head"], head_pos, h_rot)

    frame_idx = (frame_idx + 1) % total_frames
    pygame.display.flip()
    clock.tick(30)
