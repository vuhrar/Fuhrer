from typing import Optional
import os
import requests

# Adapter that supports multiple backends:
# 1) Local GGUF via llama-cpp-python (if GGUF file present)
# 2) HTTP remote local server (text-generation-webui/LM Studio)
# 3) HuggingFace transformers pipeline (fallback)

GGUF_PATH = os.getenv("GGUF_MODEL_PATH", "./models/DeepSeek-R1-Distill-Qwen-1.5B-abliterated.Q4_K_S.gguf")
WEBUI_URL = os.getenv("TEXT_GEN_WEBUI_URL", "")  # e.g. http://localhost:7860
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen-1.5B-Instruct")

try:
    if os.path.exists(GGUF_PATH):
        from llama_cpp import Llama
        _backend = "gguf"
        _llm = Llama(model_path=GGUF_PATH, n_ctx=int(os.getenv("LLM_N_CTX", "2048")))
    elif WEBUI_URL:
        _backend = "webui"
        _llm = None
    else:
        # fallback to transformers pipeline
        _backend = "transformers"
        _llm = None
        try:
            from transformers import pipeline
            # create pipeline lazily on first use to avoid heavy startup
            _pipe = None
        except Exception:
            _pipe = None
except Exception as e:
    # If import fails, mark backend unknown
    _backend = "none"
    _llm = None


class LocalLLM:
    def __init__(self):
        self.backend = _backend
        self.llm = _llm
        self.pipe = None

    def _ensure_pipeline(self):
        if self.pipe is None:
            from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
            model_name = os.getenv("HF_MODEL", HF_MODEL)
            # load pipeline -- may download weights if not cached
            try:
                self.pipe = pipeline("text-generation", model=model_name, device_map="auto")
            except Exception:
                # fallback to cpu
                self.pipe = pipeline("text-generation", model=model_name)

    def generate(self, prompt: str, temperature: float = 0.1, max_tokens: int = 512, top_k: int = 50) -> str:
        if self.backend == "gguf" and self.llm is not None:
            resp = self.llm.create(prompt=prompt, max_tokens=max_tokens, temperature=temperature, top_k=top_k)
            if isinstance(resp, dict):
                choices = resp.get("choices") or []
                if choices:
                    return choices[0].get("text", "").strip()
                return resp.get("text", "")
            return str(resp)

        elif self.backend == "webui" and os.getenv("TEXT_GEN_WEBUI_URL"):
            url = os.getenv("TEXT_GEN_WEBUI_URL").rstrip("/")
            # common webui endpoints vary; try /api/generate or /api/v1/generate
            payload = {
                "prompt": prompt,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_k": top_k,
            }
            # try a few endpoints
            for ep in ["/api/generate", "/api/v1/generate", "/generate"]:
                try:
                    r = requests.post(url + ep, json=payload, timeout=60)
                    if r.status_code == 200:
                        j = r.json()
                        # try common shapes
                        if isinstance(j, dict) and "results" in j:
                            return j["results"][0].get("text", "")
                        if isinstance(j, dict) and "data" in j:
                            return j["data"][0].get("generated_text", "")
                        if isinstance(j, dict) and "text" in j:
                            return j.get("text", "")
                        # fallback to string
                        return str(j)
                except Exception:
                    continue
            raise RuntimeError("Failed to call text-generation-webui at provided URL")

        elif self.backend == "transformers":
            # lazy load pipeline
            if self.pipe is None:
                self._ensure_pipeline()
            # models may return list of dicts
            out = self.pipe(prompt, max_new_tokens=max_tokens, temperature=temperature, do_sample=temperature>0)
            if isinstance(out, list) and out:
                # common: [{'generated_text': '...'}]
                first = out[0]
                if isinstance(first, dict):
                    return first.get("generated_text") or first.get("text") or str(first)
                return str(first)
            return str(out)

        else:
            raise RuntimeError("No valid LLM backend available. Set GGUF_MODEL_PATH, TEXT_GEN_WEBUI_URL, or HF_MODEL.")
