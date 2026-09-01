import time

class WeightFormula:
    """
    Формула ваги дії: зважує, чи варто AI-mini щось робити,
    аналізувати, відповідати, або краще заощадити токени.
    """
    def __init__(self, config: dict = None):
        self.config = config or {
            "base_weight": 1.0,
            "token_cost_per_action": 0.5,
            "complexity_penalty": 0.3,    # складні дії важчі
            "novelty_bonus": 0.2,          # нове — цікавіше
            "urgency_multiplier": 1.5,     # термінове — важливіше
            "context_overload_penalty": 0.4
        }
    
    def calculate(self, action: dict) -> dict:
        """
        action = {
            "type": "query" | "analyze" | "store" | "respond",
            "complexity": 1-10,
            "is_novel": bool,
            "is_urgent": bool,
            "context_size": int,
            "token_balance": float
        }
        """
        weight = self.config["base_weight"]
        breakdown = {}
        
        # 1. Складність — чим складніше, тим більше вага
        complexity_factor = 1 + (action.get("complexity", 1) * self.config["complexity_penalty"])
        weight *= complexity_factor
        breakdown["complexity"] = complexity_factor
        
        # 2. Новизна — нові теми отримують бонус
        if action.get("is_novel", False):
            weight *= (1 + self.config["novelty_bonus"])
            breakdown["novelty"] = self.config["novelty_bonus"]
        
        # 3. Терміновість
        if action.get("is_urgent", False):
            weight *= self.config["urgency_multiplier"]
            breakdown["urgency"] = self.config["urgency_multiplier"]
        
        # 4. Перевантаження контексту — якщо контекст забитий, вага падає
        ctx_size = action.get("context_size", 0)
        if ctx_size > 8:
            penalty = 1 - self.config["context_overload_penalty"]
            weight *= penalty
            breakdown["context_penalty"] = penalty
        
        # 5. Баланс токенів — якщо мало токенів, вага падає
        token_balance = action.get("token_balance", 100)
        if token_balance < 5:
            weight *= 0.3
            breakdown["token_penalty"] = 0.3
        elif token_balance < 20:
            weight *= 0.7
            breakdown["token_penalty"] = 0.7
        
        # 6. Вартість дії в токенах
        cost = action.get("token_cost", self.config["token_cost_per_action"])
        roi = weight / cost if cost > 0 else weight
        breakdown["roi"] = roi
        
        return {
            "weight": round(weight, 2),
            "should_act": weight >= 1.0,
            "confidence": "high" if weight >= 2.0 else "medium" if weight >= 1.0 else "low",
            "breakdown": breakdown,
            "cost": cost,
            "roi": round(roi, 2)
        }

Потім інтегруємо в ai_mini.py. Додаємо в __init__:

self.weight = WeightFormula()


І використовуємо в process() перед тим, як витрачати токени:

def process(self, user_input: str) -> str:
    # збираємо дані для формули
    action_data = {
        "type": "query",
        "complexity": self._estimate_complexity(user_input),
        "is_novel": self._is_novel(user_input),
        "is_urgent": self._is_urgent(user_input),
        "context_size": len(self.context),
        "token_balance": self.wallet.balance(),
        "token_cost": 0.5
    }
    
    # рахуємо вагу
    decision = self.weight.calculate(action_data)
    
    # якщо вага замала — не витрачаємо токени
    if not decision["should_act"]:
        return f"Вага {decision['weight']} — замало для дії. Запитай щось вагоміше."
    
    # якщо вага достатня — списуємо токени і відповідаємо
    if not self.wallet.spend(decision["cost"], f"action weight={decision['weight']}"):
        return "Недостатньо токенів."
    
    # далі звичайна логіка
    self.context.append({"role": "user", "content": user_input})
    response = self._generate_response(user_input)
    self.context.append({"role": "assistant", "content": response})
    
    return response

def _estimate_complexity(self, text: str) -> int:
    """Приблизна складність запиту 1-10"""
    length = len(text)
    if length < 20:
        return 2
    elif length < 100:
        return 5
    else:
        return 8

def _is_novel(self, text: str) -> bool:
    """Перевіряє, чи тема нова (не була в контексті)"""
    keywords = set(text.lower().split())
    for entry in self.context:
        if entry["role"] == "user":
            if keywords & set(entry["content"].lower().split()):
                return False
    return True

def _is_urgent(self, text: str) -> bool:
    """Перевіряє терміновість за ключовими словами"""
    urgent_words = ["терміново", "швидко", "строк", "дедлайн", "urgent", "now", "срочно"]
    return any(word in text.lower() for word in urgent_words)
