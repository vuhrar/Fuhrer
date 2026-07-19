import json
import logging
import time
import random
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_engine")


@dataclass
class AIPreset:
    name: str
    url: str
    model: str
    fmt: str           
    free: bool = False
    requires_key: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7
    description: str = ""


_PRESETS_RAW: List[Dict] = [
    {
        "name": "Groq LLaMA 3.3 70B 🚀 (مجاني)",
        "url": "https://groq.com",
        "model": "llama-3.3-70b-versatile", "fmt": "openai", "free": True, "requires_key": True,
        "description": "أسرع نموذج مجاني — LLaMA 70B عبر Groq"
    },
    {
        "name": "Groq LLaMA 3.1 8B ⚡ (مجاني)",
        "url": "https://groq.com",
        "model": "llama-3.1-8b-instant", "fmt": "openai", "free": True, "requires_key": True,
        "description": "خفيف وسريع جداً للمهام البسيطة"
    },
    {
        "name": "Groq Mixtral 8x7B 🔥 (مجاني)",
        "url": "https://groq.com",
        "model": "mixtral-8x7b-32768", "fmt": "openai", "free": True, "requires_key": True,
        "description": "نموذج Mixtral عبر Groq — نافذة سياق كبيرة"
    },
    {
        "name": "Claude Sonnet 3.5 🎯",
        "url": "https://anthropic.com",
        "model": "claude-3-5-sonnet-latest", "fmt": "anthropic", "free": False, "requires_key": True,
        "description": "الأفضل للتحليل القانوني المعمق"
    },
    {
        "name": "Claude Haiku 3.5 ⚡",
        "url": "https://anthropic.com",
        "model": "claude-3-5-haiku-latest", "fmt": "anthropic", "free": False, "requires_key": True,
        "description": "سريع واقتصادي من Anthropic"
    },
    {
        "name": "GPT-4o 🏆",
        "url": "https://openai.com",
        "model": "gpt-4o", "fmt": "openai", "free": False, "requires_key": True,
        "description": "الأقوى من OpenAI — متعدد الوسائط"
    },
    {
        "name": "GPT-4o Mini 💡",
        "url": "https://openai.com",
        "model": "gpt-4o-mini", "fmt": "openai", "free": False, "requires_key": True,
        "description": "اقتصادي وذكي من OpenAI"
    },
    {
        "name": "HF Qwen2.5 72B 🌟 (مجاني)",
        "url": "https://huggingface.co",
        "model": "Qwen/Qwen2.5-72B-Instruct", "fmt": "huggingface", "free": True, "requires_key": True,
        "description": "نموذج Qwen الضخم — مجاني عبر HuggingFace Inference API"
    },
    {
        "name": "HF Mistral 7B 🌊 (مجاني)",
        "url": "https://huggingface.co",
        "model": "mistralai/Mistral-7B-Instruct-v0.3", "fmt": "huggingface", "free": True, "requires_key": True,
        "description": "Mistral الموثوق — مجاني عبر HuggingFace Inference API"
    },
    {
        "name": "HF Llama 3.3 70B 🦙 (مجاني)",
        "url": "https://huggingface.co",
        "model": "meta-llama/Llama-3.3-70B-Instruct", "fmt": "huggingface", "free": True, "requires_key": True,
        "description": "Llama 3.3 من Meta — مجاني عبر HuggingFace"
    },
    {
        "name": "DeepSeek V3 💎",
        "url": "https://deepseek.com",
        "model": "deepseek-chat", "fmt": "openai", "free": False, "requires_key": True,
        "description": "DeepSeek-V3 — نموذج صيني قوي بسعر منخفض جداً"
    },
    {
        "name": "DeepSeek R1 🔬 (تفكير)",
        "url": "https://deepseek.com",
        "model": "deepseek-reasoner", "fmt": "openai", "free": False, "requires_key": True,
        "description": "DeepSeek-R1 — نموذج التفكير المتسلسل للمسائل المعقدة"
    },
    {
        "name": "Together Llama 3.3 70B ⚡",
        "url": "https://together.xyz",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "fmt": "openai", "free": False, "requires_key": True,
        "description": "Llama 3.3 70B Turbo عبر Together AI — سريع وقوي"
    },
    {
        "name": "Together Qwen 2.5 72B 🌐",
        "url": "https://together.xyz",
        "model": "Qwen/Qwen2.5-72B-Instruct-Turbo", "fmt": "openai", "free": False, "requires_key": True,
        "description": "Qwen 2.5 72B عبر Together AI — ممتاز للعربية"
    },
    {
        "name": "Together DeepSeek R1 🔬",
        "url": "https://together.xyz",
        "model": "deepseek-ai/DeepSeek-R1", "fmt": "openai", "free": False, "requires_key": True,
        "description": "DeepSeek R1 كامل عبر Together AI"
    },
    {
        "name": "Together Mixtral 8x7B 🔥",
        "url": "https://together.xyz",
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1", "fmt": "openai", "free": False, "requires_key": True,
        "description": "Mixtral 8x7B عبر Together AI — نافذة سياق كبيرة"
    },
    {
        "name": "Führer Law Brain 🧠 (محلي)",
        "url": "http://localhost:1234/v1/chat/completions",
        "model": "distil-qwen3-0.6b-shellper-q4_k_m", "fmt": "openai", "free": True, "requires_key": False,
        "description": "عقل فُهرار المتخصص — شغّل النموذج in LM Studio على جهازك ثم اتصل"
    },
    {
        "name": "⚙️ مخصص (Custom API)",
        "url": "", "model": "", "fmt": "openai", "free": False, "requires_key": True,
        "description": "اتصل بأي API متوافق مع OpenAI (LM Studio / Ollama / غيره)"
    },
    {
        "name": "Gemini 2.0 Flash ⚡",
        "url": "https://googleapis.com",
        "model": "gemini-2.0-flash", "fmt": "gemini", "free": False, "requires_key": True,
        "description": "الأسرع من Google — مثالي للردود الفورية"
    },
    {
        "name": "Gemini 1.5 Pro 🧠",
        "url": "https://googleapis.com",
        "model": "gemini-1.5-pro", "fmt": "gemini", "free": False, "requires_key": True,
        "description": "الأذكى من Google — للتحليل المعمق"
    },
]

PRESETS: Dict[str, AIPreset] = {
    p["name"]: AIPreset(**{k: v for k, v in p.items() if k != "name"}, name=p["name"])
    for p in _PRESETS_RAW
}


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    max_retries = 5
    base_delay = 2.0
    for attempt in range(max_retries):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")
            try:
                err_json = json.loads(body)
                error_msg = json.dumps(err_json, ensure_ascii=False, indent=2)
            except:
                error_msg = body[:1000]
            if e.code == 429:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"خطأ HTTP 429:\n{error_msg}")
                sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                logger.warning(f"429 error. Retry {attempt+1}/{max_retries} in {sleep_time:.2f}s")
                time.sleep(sleep_time)
                continue
            elif e.code == 404:
                raise RuntimeError(f"خطأ HTTP 404:\nالرابط: {url}\nالتفاصيل: {error_msg}")
            raise RuntimeError(f"خطأ HTTP {e.code}:\n{error_msg}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"URLError: {e.reason}")
        except TimeoutError:
            raise RuntimeError("TimeoutError")


def _build_gemini_payload(prompt: str, history: List[Dict], system: str, preset: AIPreset) -> tuple:
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
        contents.append({"role": "model", "parts": [{"text": "حسناً، أنا جاهز للمساعدة."}]})
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": str(m["content"])}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": preset.max_tokens,
            "temperature": preset.temperature,
            "topP": 0.95,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        ]
    }
    return payload, {}


def _build_anthropic_payload(prompt: str, history: List[Dict], system: str, preset: AIPreset) -> tuple:
    messages = [{"role": m["role"], "content": str(m["content"])} for m in history]
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": preset.model,
        "max_tokens": preset.max_tokens,
        "system": system,
        "messages": messages
    }
    return payload, {}


def _build_openai_payload(prompt: str, history: List[Dict], system: str, preset: AIPreset) -> tuple:
    messages = [{"role": "system", "content": system}]
    messages += [{"role": m["role"], "content": str(m["content"])} for m in history]
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": preset.model,
        "messages": messages,
        "max_tokens": preset.max_tokens,
        "temperature": preset.temperature,
    }
    return payload, {}


def _build_huggingface_payload(prompt: str, history: List[Dict], system: str, preset: AIPreset) -> tuple:
