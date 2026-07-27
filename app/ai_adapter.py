from llama_cpp import Llama
import os
from typing import Optional

class LocalLLM:
    def __init__(self, model_path: str, n_ctx: int = 2048):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        # Llama يقوم بتحميل GGUF مباشرة
        # llama-cpp-python يحتاج libgcc/clang وcmake مثبتين على النظام
        self.model = Llama(model_path=model_path, n_ctx=n_ctx)

    def generate(self, prompt: str, temperature: float = 0.1, max_tokens: int = 512, top_k: int = 50) -> str:
        resp = self.model.create(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            stop=None
        )
        # resp قد تحتوي على 'choices' أو 'text' بحسب الإصدار
        if isinstance(resp, dict):
            choices = resp.get("choices") or []
            if choices:
                return choices[0].get("text", "").strip()
            return resp.get("text", "").strip()
        return str(resp)
