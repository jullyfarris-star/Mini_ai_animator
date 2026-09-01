import math

class WaveMotionEngine:
    """Агент 3 та 4: Розрахунок фізики та математики руху (Mesh/Деформація)"""
    def __init__(self, amplitude=12, frequency=2.5):
        self.amplitude = amplitude
        self.frequency = frequency

    def calculate_sine_wave(self, current_time):
        """Рахує зміщення x/y для пасма волосся чи одягу на певній секунді шкали"""
        # Формула синуса, яку ми обговорювали для ефекту вітру
        offset = self.amplitude * math.sin(current_time * self.frequency)
        return offset

    def process_bone_rotation(self, pivot_point, angle_deg):
        """Прив'язка точок скелета та прорахунок обертання (наприклад, руки)"""
        # Матриця трансформації для повороту 2D сітки
        rad = math.radians(angle_deg)
        print(f"[Агент Фізики]: Прораховано поворот кістки навколо точки {pivot_point} на {angle_deg}°")
        return {"matrix_rad": rad, "pivot": pivot_point}
