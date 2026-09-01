import math
import random

class Ball:
    def __init__(self, x: float, y: float, vx: float = 0, vy: float = 0, 
                 radius: float = 0.03, mass: float = 1.0, number: int = 0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.mass = mass
        self.number = number
        self.active = True
    
    def kinetic_energy(self) -> float:
        return 0.5 * self.mass * (self.vx**2 + self.vy**2)
    
    def speed(self) -> float:
        return math.sqrt(self.vx**2 + self.vy**2)

class BilliardTable:
    """
    Фізичний двигун для комп'ютерного більярду.
    """
    def __init__(self, width: float = 1.0, height: float = 2.0,
                 friction: float = 0.98, restitution: float = 0.9):
        self.width = width
        self.height = height
        self.friction = friction          # тертя (1.0 = без тертя)
        self.restitution = restitution    # пружність удару
        self.balls = []
        self.pockets = [
            (0, 0), (width/2, 0), (width, 0),
            (0, height), (width/2, height), (width, height)
        ]
    
    def add_ball(self, x: float, y: float, vx: float = 0, vy: float = 0,
                 number: int = None) -> Ball:
        if number is None:
            number = len(self.balls) + 1
        ball = Ball(x, y, vx, vy, number=number)
        self.balls.append(ball)
        return ball
    
    def setup_rack(self, x: float = 0.75, y: float = 1.0):
        """Розставляє кулі трикутником (як у пулі)"""
        spacing = 0.035
        rows = 5
        for row in range(rows):
            for col in range(row + 1):
                bx = x + row * spacing * math.sqrt(3)/2
                by = y + (col - row/2) * spacing
                self.add_ball(bx, by, number=row*5 + col + 1)
    
    def cue_ball(self, x: float = 0.2, y: float = 1.0) -> Ball:
        """Біла куля"""
        ball = self.add_ball(x, y, number=0)
        return ball
    
    def shoot(self, ball: Ball, angle: float, power: float):
        """Удар по кулі: angle в радіанах, power 0-1"""
        speed = power * 2.0  # макс швидкість 2 м/с
        ball.vx = math.cos(angle) * speed
        ball.vy = math.sin(angle) * speed
    
    def update(self, dt: float = 0.01):
        """Оновлює фізику за крок dt"""
        # рух куль
        for ball in self.balls:
            if not ball.active:
                continue
            
            # тертя
            ball.vx *= self.friction
            ball.vy *= self.friction
            
            # оновлення позиції
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt
            
            # відскок від бортиків
            if ball.x - ball.radius < 0:
                ball.x = ball.radius
                ball.vx = -ball.vx * self.restitution
            elif ball.x + ball.radius > self.width:
                ball.x = self.width - ball.radius
                ball.vx = -ball.vx * self.restitution
            
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.vy = -ball.vy * self.restitution
            elif ball.y + ball.radius > self.height:
                ball.y = self.height - ball.radius
                ball.vy = -ball.vy * self.restitution
            
            # перевірка, чи в лунці
            for px, py in self.pockets:
                dist = math.sqrt((ball.x - px)**2 + (ball.y - py)**2)
                if dist < 0.05:
                    ball.active = False
                    break
        
        # зіткнення куль між собою
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                b1 = self.balls[i]
                b2 = self.balls[j]
                if not b1.active or not b2.active:
                    continue
                
                dx = b2.x - b1.x
                dy = b2.y - b1.y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < b1.radius + b2.radius and dist > 0:
                    # нормалізований вектор зіткнення
                    nx = dx / dist
                    ny = dy / dist
                    
                    # відносна швидкість
                    dvx = b1.vx - b2.vx
                    dvy = b1.vy - b2.vy
                    
                    # швидкість вздовж лінії зіткнення
                    vn = dvx * nx + dvy * ny
                    
                    if vn > 0:  # тільки якщо зближуються
                        # імпульс (пружне зіткнення)
                        impulse = (2 * vn) / (b1.mass + b2.mass)
                        
                        b1.vx -= impulse * b2.mass * nx * self.restitution
                        b1.vy -= impulse * b2.mass * ny * self.restitution
                        b2.vx += impulse * b1.mass * nx * self.restitution
                        b2.vy += impulse * b1.mass * ny * self.restitution
                        
                        # розштовхуємо, щоб не застрягли
                        overlap = (b1.radius + b2.radius - dist) / 2
                        b1.x -= overlap * nx
                        b1.y -= overlap * ny
                        b2.x += overlap * nx
                        b2.y += overlap * ny
    
    def simulate(self, steps: int = 100) -> list:
        """Повна симуляція, повертає історію позицій"""
        history = []
        for _ in range(steps):
            self.update(0.02)
            snapshot = [(b.x, b.y, b.active) for b in self.balls]
            history.append(snapshot)
        return history
    
    def predict_trajectory(self, ball: Ball, steps: int = 50) -> list:
        """Прогнозує траєкторію кулі"""
        trajectory = []
        sim_x, sim_y = ball.x, ball.y
        sim_vx, sim_vy = ball.vx, ball.vy
        
        for _ in range(steps):
            sim_vx *= self.friction
            sim_vy *= self.friction
            sim_x += sim_vx * 0.02
            sim_y += sim_vy * 0.02
            
            # відскок
            if sim_x < 0 or sim_x > self.width:
                sim_vx = -sim_vx * self.restitution
            if sim_y < 0 or sim_y > self.height:
                sim_vy = -sim_vy * self.restitution
            
            trajectory.append((sim_x, sim_y))
        
        return trajectory



Інтегруємо в ai_mini.py:

self.billiard = BilliardTable()

починає видавати сміття.

Крок 15: Safeguard для Black Box

Додаємо в core/safeguards.py новий клас 

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


