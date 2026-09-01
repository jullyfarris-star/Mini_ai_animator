import os
import json
import base64

def image_to_base64(img_path):
    """Перетворює деталі персонажа в текст для роботи без сервера"""
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"
    return ""

def generate_html5_interactive_package():
    base_dir = os.path.join("data", "animations", "scenario_5")
    json_path = os.path.join(base_dir, "skeleton.json")
    textures_dir = os.path.join(base_dir, "textures")
    html_output = os.path.join(base_dir, "index.html")
    
    if not os.path.exists(json_path):
        print("❌ Спочатку запустіть перший скрипт core/spine_pipeline.py!")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        spine_data = json.load(f)

    parts = ["body", "head", "arm_left", "arm_right"]
    base64_textures = {}
    for part in parts:
        tex_path = os.path.join(textures_dir, f"{part}.png")
        base64_textures[part] = image_to_base64(tex_path)

    html_content = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aelis Spine WebGL Viewport</title>
    <style>
        body {{ margin: 0; padding: 0; background-color: #121214; overflow: hidden; display: flex; justify-content: center; align-items: center; height: 100vh; width: 100vw; font-family: sans-serif; user-select: none; -webkit-user-select: none; }}
        #canvas-container {{ box-shadow: 0 25px 60px rgba(0,0,0,0.8); border-radius: 12px; overflow: hidden; border: 2px solid #25252b; touch-action: none; }}
        #panel {{ position: absolute; top: 20px; left: 20px; color: #fff; background: rgba(20, 20, 25, 0.9); padding: 15px 20px; border-radius: 8px; border-left: 4px solid #00e5ff; pointer-events: none; }}
        h3 {{ margin: 0 0 5px 0; color: #00e5ff; font-size: 16px; }}
        p {{ margin: 3px 0; font-size: 13px; color: #ccc; }}
        #toggle-btn {{ position: absolute; bottom: 30px; left: 30px; background: #25252b; color: #00e5ff; border: 2px solid #00e5ff; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: all 0.2s ease; }}
        #toggle-btn:hover {{ background: #00e5ff; color: #121214; }}
    </style>
    <script src="https://cloudflare.com"></script>
</head>
<body>
    <div id="panel">
        <h3>📐 Aelis Spine Viewport</h3>
        <p>• <b>Сценарій:</b> №5 (Візуалізація кісток)</p>
        <p>• <b>Керування:</b> Тягніть мишкою або пальцем</p>
    </div>
    <button id="toggle-btn" onclick="toggleBones()">🦴 Сховати Скелет</button>
    <div id="canvas-container"></div>

    <script>
        const spineData = {json.dumps(spine_data)};
        const textureAssets = {json.dumps(base64_textures)};

        const app = new PIXI.Application({{ width: 800, height: 600, backgroundColor: 0x18181c, resolution: window.devicePixelRatio || 1, autoDensity: true }});
        document.getElementById('canvas-container').appendChild(app.view);

        const container = new PIXI.Container();
        app.stage.addChild(container);

        const skeletonOverlay = new PIXI.Graphics();
        app.stage.addChild(skeletonOverlay);

        let frameIdx = 0; const totalFrames = 60; const meshes = {{}}; let showBones = true;
        const dragOffsets = {{ body: {{x:0,y:0}}, head: {{x:0,y:0}}, arm_left: {{x:0,y:0}}, arm_right: {{x:0,y:0}} }};
        let draggedBone = null; let dragStartMouse = {{x:0,y:0}}; let dragStartOffset = {{x:0,y:0}};

        const bonesMap = {{}}; spineData.bones.forEach(b => {{ bonesMap[b.name] = b; }});
        const skinSlots = spineData.skins.default;
        const animAttachments = spineData.animations.scenario_5_idle_action.attachments;

        Object.keys(skinSlots).forEach(name => {{
            const meta = skinSlots[name][name];
            const geometry = new PIXI.Geometry()
                .addAttribute('aVertexPosition', new Float32Array(meta.vertices), 2)
                .addAttribute('aTextureCoord', new Float32Array(meta.uvs), 2)
                .addIndex(new Uint16Array(meta.triangles));

            const baseTexture = PIXI.BaseTexture.from(textureAssets[name] || PIXI.Texture.WHITE);
            const shader = PIXI.Shader.from(
                `precision mediump float; attribute vec2 aVertexPosition; attribute vec2 aTextureCoord; uniform mat3 translationMatrix; uniform mat3 projectionMatrix; varying vec2 vTextureCoord; void main() {{ vTextureCoord = aTextureCoord; gl_Position = vec4((projectionMatrix * translationMatrix * vec3(aVertexPosition, 1.0)).xy, 0.0, 1.0); }}`,
                `varying vec2 vTextureCoord; uniform sampler2D uSampler; void main() {{ gl_FragColor = texture2D(uSampler, vTextureCoord); }}`
            );

            const pixiMesh = new PIXI.Mesh(geometry, shader);
            pixiMesh.interactive = true; pixiMesh.buttonMode = true; pixiMesh.boneName = name;
            pixiMesh.on('pointerdown', (e) => {{ draggedBone = e.currentTarget.boneName; dragStartMouse = e.data.getLocalPosition(app.stage); dragStartOffset = {{...dragOffsets[draggedBone]}}; }});

            container.addChild(pixiMesh);
            meshes[name] = {{ mesh: pixiMesh, baseVertices: meta.vertices, meta: meta }};
        }});

        app.stage.interactive = true;
        app.stage.on('pointermove', (e) => {{ if (!draggedBone) return; const m = e.data.getLocalPosition(app.stage); dragOffsets[draggedBone].x = dragStartOffset.x + (m.x - dragStartMouse.x); dragOffsets[draggedBone].y = dragStartOffset.y + (m.y - dragStartMouse.y); }});
        app.stage.on('pointerup', () => {{ draggedBone = null; }}); app.stage.on('pointerupoutside', () => {{ draggedBone = null; }});

        window.toggleBones = function() {{ showBones = !showBones; document.getElementById('toggle-btn').innerText = showBones ? "🦴 Сховати Скелет" : "🦴 Показати Скелет"; if(!showBones) skeletonOverlay.clear(); }};

        app.ticker.add(() => {{
            const currentFrame = Math.floor(frameIdx) % totalFrames;
            const bPosLog = {{}};
            const rx = bonesMap.root.x, ry = app.screen.height - bonesMap.root.y;

            Object.keys(skinSlots).forEach(name => {{
                const item = meshes[name];
                const offsets = animAttachments[name][name].mesh[currentFrame].vertices;
                const positions = item.mesh.geometry.getBuffer('aVertexPosition').data;

                let cx = rx + bonesMap.body.x + dragOffsets.body.x;
                let cy = ry - bonesMap.body.y + dragOffsets.body.y;
                if (name !== "body") {{ cx += bonesMap[name].x + dragOffsets[name].x; cy -= bonesMap[name].y - dragOffsets[name].y; }}
                bPosLog[name] = {{x: cx, y: cy}};

                for (let i = 0; i < positions.length; i += 2) {{
                    positions[i] = cx + item.baseVertices[i] + (offsets[i] || 0);
                    positions[i+1] = cy + item.baseVertices[i+1] + (offsets[i+1] || 0);
                }}
                item.mesh.geometry.getBuffer('aVertexPosition').update();
            }});

            if (showBones && bPosLog["body"]) {{
                skeletonOverlay.clear();
                skeletonOverlay.lineStyle(4, 0x00e5ff, 1); skeletonOverlay.moveTo(rx, ry); skeletonOverlay.lineTo(bPosLog["body"].x, bPosLog["body"].y);
                if(bPosLog["head"]) {{ skeletonOverlay.lineStyle(3, 0xff00ff, 1); skeletonOverlay.moveTo(bPosLog["body"].x, bPosLog["body"].y); skeletonOverlay.lineTo(bPosLog["head"].x, bPosLog["head"].y); }}
                if(bPosLog["arm_left"]) {{ skeletonOverlay.lineStyle(3, 0xffff00, 1); skeletonOverlay.moveTo(bPosLog["body"].x, bPosLog["body"].y); skeletonOverlay.lineTo(bPosLog["arm_left"].x, bPosLog["arm_left"].y); }}
                if(bPosLog["arm_right"]) {{ skeletonOverlay.lineStyle(3, 0xffff00, 1); skeletonOverlay.moveTo(bPosLog["body"].x, bPosLog["body"].y); skeletonOverlay.lineTo(bPosLog["arm_right"].x, bPosLog["arm_right"].y); }}
                skeletonOverlay.lineStyle(0);
                skeletonOverlay.beginFill(0x00ff87); skeletonOverlay.drawCircle(rx, ry, 7);
                skeletonOverlay.beginFill(0x00e5ff); skeletonOverlay.drawCircle(bPosLog["body"].x, bPosLog["body"].y, 6);
                if(bPosLog["head"]) {{ skeletonOverlay.beginFill(0xff00ff); skeletonOverlay.drawCircle(bPosLog["head"].x, bPosLog["head"].y, 6); }}
                if(bPosLog["arm_left"]) {{ skeletonOverlay.beginFill(0xffff00); skeletonOverlay.drawCircle(bPosLog["arm_left"].x, bPosLog["arm_left"].y, 6); }}
                if(bPosLog["arm_right"]) {{ skeletonOverlay.beginFill(0xffff00); skeletonOverlay.drawCircle(bPosLog["arm_right"].x, bPosLog["arm_right"].y, 6); }}
                skeletonOverlay.endFill();
            }}
            frameIdx += 0.5;
        }});
    </script>
</body>
</html>
"""

    with open(html_output, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"🌐 Фінальну інтерактивну сторінку створено в: {html_output}")

if __name__ == "__main__":
    generate_html5_interactive_package()
