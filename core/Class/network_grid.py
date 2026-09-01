import json
import time
import os

class NetworkGrid:
    """
    Сітка, на якій будується нейромережа.
    Кожен вузол — це модуль (шар, сервіс, плагін).
    Кожне ребро — це зв'язок між модулями.
    """
    def __init__(self, path: str = "data/network_grid.json"):
        self.path = path
        self.grid = self._load()
    
    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "nodes": [],
            "edges": [],
            "layers": [],
            "created_at": time.time(),
            "version": 1
        }
    
    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.grid, f, indent=2, ensure_ascii=False)
    
    def add_node(self, node: dict) -> str:
        """
        node = {
            "id": "embedding_01",
            "type": "embedding" | "attention" | "ffn" | "service" | "plugin",
            "layer": 0,
            "config": {},
            "active": True
        }
        """
        if "id" not in node:
            node["id"] = f"node_{len(self.grid['nodes'])}"
        node["added_at"] = time.time()
        self.grid["nodes"].append(node)
        self._save()
        return node["id"]
    
    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0):
        """Зв'язок між двома вузлами"""
        self.grid["edges"].append({
            "source": source_id,
            "target": target_id,
            "weight": weight,
            "active": True
        })
        self._save()
    
    def add_layer(self, name: str, depth: int):
        """Додає шар у сітку"""
        self.grid["layers"].append({
            "name": name,
            "depth": depth,
            "nodes": []
        })
        self._save()
    
    def connect_node_to_layer(self, node_id: str, layer_name: str):
        """Прив'язує вузол до шару"""
        for layer in self.grid["layers"]:
            if layer["name"] == layer_name:
                if node_id not in layer["nodes"]:
                    layer["nodes"].append(node_id)
                break
        self._save()
    
    def get_layer(self, depth: int) -> list:
        """Повертає всі вузли на певній глибині"""
        nodes = []
        for layer in self.grid["layers"]:
            if layer["depth"] == depth:
                for node_id in layer["nodes"]:
                    for node in self.grid["nodes"]:
                        if node["id"] == node_id:
                            nodes.append(node)
        return nodes
    
    def grow(self, template: str = "transformer"):
        """Автоматично вирощує базову структуру за шаблоном"""
        if template == "transformer":
            # Input layer
            self.add_layer("input", 0)
            # Embedding
            emb_id = self.add_node({
                "id": "embedding",
                "type": "embedding",
                "layer": 0,
                "config": {"dim": 512}
            })
            self.connect_node_to_layer(emb_id, "input")
            
            # Attention layer
            self.add_layer("attention", 1)
            att_id = self.add_node({
                "id": "self_attention",
                "type": "attention",
                "layer": 1,
                "config": {"heads": 8}
            })
            self.connect_node_to_layer(att_id, "attention")
            self.add_edge(emb_id, att_id, 1.0)
            
            # FFN layer
            self.add_layer("ffn", 2)
            ffn_id = self.add_node({
                "id": "feed_forward",
                "type": "ffn",
                "layer": 2,
                "config": {"hidden_dim": 2048}
            })
            self.connect_node_to_layer(ffn_id, "ffn")
            self.add_edge(att_id, ffn_id, 1.0)
            
            # Output layer
            self.add_layer("output", 3)
            out_id = self.add_node({
                "id": "linear_output",
                "type": "linear",
                "layer": 3,
                "config": {"vocab_size": 32000}
            })
            self.connect_node_to_layer(out_id, "output")
            self.add_edge(ffn_id, out_id, 1.0)
    
    def status(self) -> dict:
        return {
            "nodes": len(self.grid["nodes"]),
            "edges": len(self.grid["edges"]),
            "layers": len(self.grid["layers"]),
            "version": self.grid["version"]
        }



Потім інтегруємо в ai_mini.py. Додаємо в __init__:

self.grid = NetworkGrid()
# при старті вирощуємо базовий трансформер
if len(self.grid.status()["nodes"]) == 0:
    self.grid.grow("transformer")


І додаємо метод для додавання нових модулів на льоту:

def grow_network(self, module_type: str, config: dict = None) -> str:
    """Додає новий модуль у сітку"""
    node = {
        "type": module_type,
        "config": config or {},
        "active": True
    }
    node_id = self.grid.add_node(node)
    
    # автоматично підключаємо до останнього шару
    layers = self.grid.grid["layers"]
    if layers:
        last_layer = layers[-1]
        self.grid.connect_node_to_layer(node_id, last_layer["name"])
        # зв'язуємо з останнім вузлом у шарі
        if last_layer["nodes"]:
            last_node_id = last_layer["nodes"][-1]
            self.grid.add_edge(last_node_id, node_id, 0.5)
    
    return f"Модуль {node_id} додано в сітку"
