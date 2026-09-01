import json
import time

class AIMini:
    def __init__(self, config_path: str = "config/cube_dna.json"):
        self.dna = self._load_dna(config_path)
        self.context = []
        self.state = self.dna["states"]["system"][0]  # "stable"
        self.last_active = time.time()
    
    def _load_dna(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def process(self, user_input: str) -> str:
        # оновлюємо час активності
        self.last_active = time.time()
        
        # додаємо вхідне повідомлення в контекст
        self.context.append({"role": "user", "content": user_input})
        
        # обрізаємо контекст до ліміту
        max_ctx = self.dna["rules"]["style"]["max_context"]
        if len(self.context) > max_ctx:
            self.context = self.context[-max_ctx:]
        
        # логіка відповіді (поки що заглушка)
        response = self._generate_response(user_input)
        
        # додаємо відповідь у контекст
        self.context.append({"role": "assistant", "content": response})
        
        return response
    
    def _generate_response(self, user_input: str) -> str:
        # тут буде гібридна логіка — поки просто дзеркало
        return f"Куб отримав: {user_input}"
    
    def status(self) -> dict:
        return {
            "state": self.state,
            "context_size": len(self.context),
            "last_active": self.last_active,
            "dna_version": self.dna["cube_dna"]["version"]
        }


