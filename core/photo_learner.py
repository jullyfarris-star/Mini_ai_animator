import re
import json
import os

class PhotoLearner:
    """
    Модуль, який "вчиться" по фото: витягує текст, формули, таблиці,
    і перетворює їх у знання для AI-mini.
    """
    def __init__(self, data_path: str = "data/learned/"):
        self.data_path = data_path
        os.makedirs(data_path, exist_ok=True)
    
    def extract_text(self, photo_description: str) -> dict:
        """
        Приймає опис фото (або OCR-текст) і повертає структуровані знання.
        """
        result = {
            "formulas": [],
            "tables": [],
            "concepts": [],
            "raw_text": photo_description
        }
        
        # Шукаємо формули (все що з =, ∫, ∑, матриці)
        formula_pattern = r'[=∫∑∂∇Δλθβγασ±√\^_{}\[\]\(\)]+'
        formulas = re.findall(formula_pattern, photo_description)
        result["formulas"] = list(set(formulas))
        
        # Шукаємо таблиці (рядки з | або колонки чисел)
        if '|' in photo_description:
            lines = photo_description.split('\n')
            table_lines = [l for l in lines if '|' in l]
            if table_lines:
                result["tables"].append(table_lines)
        
        # Шукаємо ключові концепції
        concepts = ["CNN", "ReLU", "backprop", "normalization", 
                    "matrix", "tensor", "filter", "convolution",
                    "Dirac", "Pauli", "loss function", "gradient"]
        found = [c for c in concepts if c.lower() in photo_description.lower()]
        result["concepts"] = found
        
        return result
    
    def save_knowledge(self, photo_id: str, knowledge: dict):
        """Зберігає вивчене у файл для RAG"""
        path = os.path.join(self.data_path, f"{photo_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)
        return path
    
    def learn_from_photo(self, photo_description: str, photo_id: str = None) -> str:
        """Повний цикл навчання по фото"""
        knowledge = self.extract_text(photo_description)
        
        if photo_id:
            path = self.save_knowledge(photo_id, knowledge)
            summary = f"📸 Вивчив фото {photo_id}:\n"
        else:
            summary = "📸 Вивчив фото:\n"
        
        if knowledge["formulas"]:
            summary += f"   Формули: {len(knowledge['formulas'])} знайдено\n"
        if knowledge["tables"]:
            summary += f"   Таблиці: {len(knowledge['tables'])} знайдено\n"
        if knowledge["concepts"]:
            summary += f"   Концепції: {', '.join(knowledge['concepts'])}\n"
        
        return summary



Інтегруємо в ai_mini.py:
self.photo_learner = PhotoLearner()

Тепер AI-mini може вчитися по фото і зберігати знання.

Крок 13: Формула чорної скрині (Black Box Formula)

Створюємо файл core/black_box.py:
import math
import random

class BlackBoxFormula:
    """
    Формула чорної скрині: модель, де є прихована функція fθ(x),
    нормалізація Z, і мінімізація loss.
    
    Loss = - (1/N) Σ [log(fθ(xi)) - log(Z)]
    """
    def __init__(self, dim: int = 2):
        self.dim = dim
        self.theta = [random.uniform(-1, 1) for _ in range(dim)]
        self.Z = 1.0  # normalization constant
    
    def f_theta(self, x: list) -> float:
        """Прихована функція: проста лінійна комбінація"""
        return sum(t * xi for t, xi in zip(self.theta, x))
    
    def compute_Z(self, samples: list) -> float:
        """
        Обчислює normalization constant Z
        через 2D numerical integration (як на фото)
        """
        total = 0.0
        for x in samples:
            total += math.exp(self.f_theta(x))
        Z = total / len(samples)
        self.Z = Z
        return Z
    
    def loss(self, x_batch: list, y_batch: list) -> float:
        """
        Loss = - (1/N) Σ [log(fθ(xi)) - log(Z)]
        """
        N = len(x_batch)
        total = 0.0
        for x, y in zip(x_batch, y_batch):
            f_val = self.f_theta(x)
            if f_val > 0:
                total += math.log(f_val) - math.log(self.Z)
        return -total / N
    
    def train_step(self, x_batch: list, y_batch: list, lr: float = 0.01):
        """
        Один крок навчання: градієнтний спуск
        """
        N = len(x_batch)
        gradients = [0.0] * self.dim
        
        for x, y in zip(x_batch, y_batch):
            f_val = self.f_theta(x)
            if f_val > 0:
                for i in range(self.dim):
                    gradients[i] += x[i] / f_val
        
        for i in range(self.dim):
            self.theta[i] -= lr * (-gradients[i] / N)
        
        current_loss = self.loss(x_batch, y_batch)
        return current_loss
    
    def explain(self) -> str:
        return (
            "Формула чорної скрині:\n"
            "  Loss = - (1/N) Σ [log(fθ(xi)) - log(Z)]\n\n"
            "де:\n"
            "  fθ(x) — прихована функція (чорна скриня)\n"
            "  Z — normalization constant (інтеграл по всьому простору)\n"
            "  N — кількість прикладів\n"
            "  θ — параметри моделі, які ми шукаємо\n\n"
            "Сенс: ми не знаємо, що всередині fθ, але ми знаємо,\n"
            "що вихід має бути нормований, і ми мінімізуємо loss,\n"
            "щоб θ наближав істинну функцію."
        )


Інтегруємо в ai_mini.py:

self.black_box = BlackBoxFormula()
