# ai_engine.py
"""
محرك الاتصال بالنماذج الاصطناعية.
يدعم: Gemini, Groq, Claude, OpenAI, Hugging Face (مجاني)
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict

logger = logging.getLogger("ai_engine")

# قائمة النماذج المتاحة
PRESETS = {
    "Gemini 2.0 Flash — نجاني": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "model": "gemini-2.0-flash", "fmt": "gemini", "free": False, "requires_key": True
    },
    "Gemini 1.5 Pro — نجاني": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        "model": "gemini-1.5-pro", "fmt": "gemini", "free": False, "requires_key": True
    },
    "Groq LLaMA 3.3 — سريع مجاني": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile", "fmt": "openai", "free": True, "requires_key": True
    },
    "Groq Mixtral 8x7B — سريع مجاني": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "mixtral-8x7b-32768", "fmt": "openai", "free": True, "requires_key": True
    },
    "Claude Sonnet — أنثروبيك": {
        "url": "https://api.anthropic.com/v1/messages", "model": "claude-sonnet-4-6",
        "fmt": "anthropic", "free": False, "requires_key": True
    },
    "Claude Haiku — أنثروبيك": {
        "url": "https://api.anthropic.com/v1/messages", "model": "claude-haiku-4-0",
        "fmt": "anthropic", "free": False, "requires_key": True
    },
    "OpenAI GPT-4o — أوبن أي": {
        "url": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o",
        "fmt": "openai", "free": False, "requires_key": True
    },
    "OpenAI GPT-3.5 — أوبن أي": {
        "url": "https://api.openai.com/v1/chat/completions", "model": "gpt-3.5-turbo",
        "fmt": "openai", "free": False, "requires_key": True
    },
    "Hugging Face - Qwen2.5 7B": {
        "url": "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct",
        "model": "Qwen/Qwen2.5-7B-Instruct", "fmt": "huggingface", "free": True, "requires_key": True
    },
    "Hugging Face - Mistral 7B": {
        "url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
        "model": "mistralai/Mistral-7B-Instruct-v0.2", "fmt": "huggingface", "free": True, "requires_key": True
    },
    "Hugging Face - Llama 3.2 3B": {
        "url": "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3.2-3B-Instruct",
        "model": "meta-llama/Meta-Llama-3.2-3B-Instruct", "fmt": "huggingface", "free": True, "requires_key": True
    },
    "⚙️ مخصص": {"url": "", "model": "", "fmt": "openai", "free": False, "requires_key": True}
}

def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")[:800]
        raise RuntimeError(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URLError: {e.reason}")

def call_ai(prompt: str, history: List[Dict], system: str,
            preset_name: str, api_key: str,
            custom_url: str = "", custom_model: str = "", custom_fmt: str = "openai") -> str:
    preset = PRESETS.get(preset_name, PRESETS["⚙️ مخصص"])
    url = custom_url if preset_name == "⚙️ مخصص" else preset["url"]
    model = custom_model if preset_name == "⚙️ مخصص" else preset["model"]
    fmt = custom_fmt if preset_name == "⚙️ مخصص" else preset["fmt"]

    if not api_key and preset.get("requires_key", True):
        return "❌ لم يتم إدخال مفتاح API. أدخله من زر الإعدادات (⚙️)."
    if not url:
        return "❌ لم يتم تحديد رابط API. راجعه من الإعدادات."

    clean_history = [{"role": m["role"], "content": m["content"]} for m in history]

    try:
        if fmt == "gemini":
            contents = []
            if system:
                contents.append({"role": "user", "parts": [{"text": system}]})
                contents.append({"role": "model", "parts": [{"text": "حسناً، أنا جاهز للمساعدة."}]})
            for m in clean_history:
                role = "model" if m["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            payload = {"contents": contents, "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.7}}
            resp = _post_json(f"{url}?key={api_key}", payload, {"Content-Type": "application/json"})
            return resp["candidates"][0]["content"]["parts"][0]["text"]

        elif fmt == "anthropic":
            messages = clean_history + [{"role": "user", "content": prompt}]
            payload = {"model": model, "max_tokens": 4096, "system": system, "messages": messages}
            headers = {"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"}
            resp = _post_json(url, payload, headers)
            return resp["content"][0]["text"]

        elif fmt == "huggingface":
            full_prompt = f"<s>[INST] {system} [/INST]\n"
            for msg in [{"role": "system", "content": system}] + clean_history + [{"role": "user", "content": prompt}]:
                if msg["role"] == "system":
                    continue
                full_prompt += f"\n<s>[INST] {msg['content']} [/INST]"
            payload = {"inputs": full_prompt, "parameters": {"max_new_tokens": 512, "temperature": 0.7}}
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            resp = _post_json(url, payload, headers)
            if isinstance(resp, list) and len(resp) > 0:
                return resp[0].get("generated_text", "")
            return str(resp)

        else:  # openai-compatible
            messages = [{"role": "system", "content": system}] + clean_history + [{"role": "user", "content": prompt}]
            payload = {"model": model, "messages": messages, "max_tokens": 4096, "temperature": 0.7}
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            resp = _post_json(url, payload, headers)
            return resp["choices"][0]["message"]["content"]

    except RuntimeError as e:
        err = str(e)
        if "429" in err:
            return "⏳ الطلبات كثيرة جداً (Rate Limit). انتظر قليلاً ثم حاول مجدداً."
        if "401" in err or "403" in err:
            return "🔑 مفتاح API غير صحيح أو منتهي الصلاحية."
        if "404" in err:
            return f"🔗 رابط API غير صحيح أو النموذج غير موجود:\n`{url}`"
        return f"❌ خطأ في الاتصال:\n{err[:400]}"
    except KeyError as e:
        return f"❌ استجابة غير متوقعة من الخادم (مفتاح مفقود: {e})."
    except Exception as e:
        return f"❌ خطأ غير متوقع: {str(e)[:300]}"

def get_preset_info(preset_name: str) -> Dict:
    preset = PRESETS.get(preset_name, {})
    return {
        "name": preset_name,
        "url": preset.get("url", ""),
        "model": preset.get("model", ""),
        "fmt": preset.get("fmt", ""),
        "free": preset.get("free", False),
        "requires_key": preset.get("requires_key", True)
    }

def get_free_models() -> List[Dict]:
    return [{"name": name, "model": p["model"], "fmt": p["fmt"], "requires_key": p["requires_key"]}
            for name, p in PRESETS.items() if p.get("free", False)]

def get_paid_models() -> List[Dict]:
    return [{"name": name, "model": p["model"], "fmt": p["fmt"], "requires_key": p["requires_key"]}
            for name, p in PRESETS.items() if not p.get("free", False)]