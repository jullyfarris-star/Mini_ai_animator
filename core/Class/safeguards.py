class BlackBoxSafeguard:
    """
    Запобіжник для чорної скрині.
    Слідкує, щоб loss не зростав, параметри не розходились,
    і normalization constant Z не ставав нулем або нескінченністю.
    """
    def __init__(self, config: dict = None):
        self.config = config or {
            "max_loss": 10.0,                # якщо loss вище — тривога
            "max_theta_growth": 5.0,         # якщо параметри виросли в 5 разів
            "min_Z": 1e-6,                   # мінімальна нормалізація
            "max_Z": 1e6,                    # максимальна нормалізація
            "loss_growth_threshold": 0.5,    # якщо loss виріс на 50% за крок
            "patience": 3                    # скільки разів можна помилятись
        }
        self.violations = 0
        self.last_loss = None
        self.locked = False                  # блокування, якщо все погано
    
    def check(self, black_box) -> dict:
        """
        Перевіряє стан чорної скрині.
        Повертає звіт: чи все ок, що не так, чи треба блокувати.
        """
        if self.locked:
            return {
                "safe": False,
                "locked": True,
                "reason": "Чорна скриня заблокована після попередніх порушень"
            }
        
        issues = []
        
        # 1. Перевірка Z (normalization constant)
        Z = getattr(black_box, 'Z', 1.0)
        if Z < self.config["min_Z"]:
            issues.append(f"Z занадто малий: {Z:.6f} < {self.config['min_Z']}")
        if Z > self.config["max_Z"]:
            issues.append(f"Z занадто великий: {Z:.6f} > {self.config['max_Z']}")
        
        # 2. Перевірка theta (параметри)
        theta = getattr(black_box, 'theta', [])
        if theta:
            max_theta = max(abs(t) for t in theta)
            if max_theta > self.config["max_theta_growth"]:
                issues.append(f"Параметри розходяться: max θ = {max_theta:.2f}")
        
        # 3. Перевірка loss
        current_loss = getattr(black_box, 'last_loss', None)
        if current_loss is not None:
            if current_loss > self.config["max_loss"]:
                issues.append(f"Loss занадто високий: {current_loss:.4f}")
            
            if self.last_loss is not None and self.last_loss > 0:
                growth = (current_loss - self.last_loss) / self.last_loss
                if growth > self.config["loss_growth_threshold"]:
                    issues.append(f"Loss зріс на {growth*100:.0f}% за крок")
        
        # 4. Перевірка, чи loss взагалі змінюється
        if self.last_loss is not None and current_loss is not None:
            if abs(current_loss - self.last_loss) < 1e-10:
                issues.append("Loss не змінюється — можливо, застряг у локальному мінімумі")
        
        # оновлюємо стан
        self.last_loss = current_loss
        
        if issues:
            self.violations += 1
            if self.violations >= self.config["patience"]:
                self.locked = True
                return {
                    "safe": False,
                    "locked": True,
                    "violations": self.violations,
                    "issues": issues,
                    "reason": "Перевищено ліміт порушень — чорна скриня заблокована"
                }
            
            return {
                "safe": False,
                "locked": False,
                "violations": self.violations,
                "issues": issues,
                "reason": f"Знайдено {len(issues)} проблем"
            }
        
        # все добре
        self.violations = 0
        return {
            "safe": True,
            "locked": False,
            "violations": 0,
            "issues": [],
            "reason": "Чорна скриня стабільна"
        }
    
    def reset(self):
        """Скидає запобіжник (після виправлення проблем)"""
        self.violations = 0
        self.last_loss = None
        self.locked = False
    
    def explain(self) -> str:
        return (
            "Запобіжник чорної скрині перевіряє:\n"
            "  1. Normalization constant Z — не нуль і не нескінченність\n"
            "  2. Параметри θ — не розходяться\n"
            "  3. Loss — не зростає різко\n"
            "  4. Loss — змінюється (не застряг)\n\n"
            f"Після {self.config['patience']} порушень — блокує чорну скриню."
        )


Потім інтегруємо в ai_mini.py. Додаємо в __init__:

self.bb_safeguard = BlackBoxSafeguard()

І в метод, який викликає чорну скриню:

def train_black_box(self, x_batch, y_batch):
    # спочатку перевіряємо запобіжник
    check = self.bb_safeguard.check(self.black_box)
    
    if not check["safe"]:
        if check["locked"]:
            return f"⛔ {check['reason']}. Скинь запобіжник перед продовженням."
        return f"⚠️ {check['reason']}. Будь обережний."
    
    # якщо все ок — тренуємо
    loss = self.black_box.train_step(x_batch, y_batch)
    self.black_box.last_loss = loss
    
    # перевіряємо після кроку
    post_check = self.bb_safeguard.check(self.black_box)
    if not post_check["safe"]:
        return f"⚠️ Після кроку: {post_check['reason']}. Loss: {loss:.4f}"
    
    return f"✅ Крок успішний. Loss: {loss:.4f}"


