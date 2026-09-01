# core/llm.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict

class LocalLLM:
    def __init__(self, model_name: str = "Qwen/Qwen2-1.5B-Instruct", device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 Завантаження {model_name} на {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True
        )
        if self.device == "cpu":
            self.model.to("cpu")
        self.model.eval()
        print("✅ LLM завантажено!")

    def generate(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.7) -> str:
        messages = [
            {"role": "system", "content": "Ти — AI-Міні, розумний та дружній помічник. Відповідай лаконічно та по суті."},
            {"role": "user", "content": prompt}
        ]
        # Застосовуємо chat template
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return response.strip()

