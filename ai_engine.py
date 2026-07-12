# ai_engine.py
"""
محرك الاتصال بنماذج الذكاء الاصطناعي — النسخة الاحترافية v2.0
يدعم: Gemini, Groq, Claude, OpenAI, Hugging Face
المبادئ المطبقة: Factory Pattern, Single Responsibility, Clean Error Handling
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field

# ============================================================
# إعداد نظام التسجيل (Logging)
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_engine")


# ============================================================
# نموذج بيانات الإعداد (Data Model)
# ============================================================
@dataclass
class AIPreset:
    """نموذج بيانات موحد لإعدادات النموذج"""
    name: str
    url: str
    model: str
    fmt: str           # openai | gemini | anthropic | huggingface
    free: bool = False
    requires_key: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7
    description: str = ""


# ============================================================
# سجل النماذج المتاحة (Model Registry)
# ============================================================
_PRESETS_RAW: List[Dict] = [
    # --- Google Gemini ---
    {
        "name": "Gemini 2.0 Flash ⚡",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "model": "gemini-2.0-flash", "fmt": "gemini", "free": False, "requires_key": True,
        "description": "الأسرع من Google — مثالي للردود الفورية"
    },
    {
        "name": "Gemini 1.5 Pro 🧠",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        "model": "gemini-1.5-pro", "fmt": "gemini", "free": False, "requires_key": True,
        "description": "الأذكى من Google — للتحليل المعمق"
    },
    # --- Groq (مجاني وسريع) ---
    {
        "name": "Groq LLaMA 3.3 70B 🚀 (مجاني)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile", "fmt": "openai", "free": True, "requires_key": True,
        "description": "أسرع نموذج مجاني — LLaMA 70B عبر Groq"
    },
    {
        "name": "Groq LLaMA 3.1 8B ⚡ (مجاني)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.1-8b-instant", "fmt": "openai", "free": True, "requires_key": True,
        "description": "خفيف وسريع جداً للمهام البسيطة"
    },
    {
        "name": "Groq Mixtral 8x7B 🔥 (مجاني)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "mixtral-8x7b-32768", "fmt": "openai", "free": True, "requires_key": True,
        "description": "نموذج Mixtral عبر Groq — نافذة سياق كبيرة"
    },
    # --- Anthropic Claude ---
    {
        "name": "Claude Sonnet 4 🎯",
        "url": "https://api.anthropic.com/v1/messages",
        "model": "claude-sonnet-4-6", "fmt": "anthropic", "free": False, "requires_key": True,
        "description": "الأفضل للتحليل القانوني المعمق"
    },
    {
        "name": "Claude Haiku 4 ⚡",
        "url": "https://api.anthropic.com/v1/messages",
        "model": "claude-haiku-4-0", "fmt": "anthropic", "free": False, "requires_key": True,
        "description": "سريع واقتصادي من Anthropic"
    },
    # --- OpenAI ---
    {
        "name": "GPT-4o 🏆",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o", "fmt": "openai", "free": False, "requires_key": True,
        "description": "الأقوى من OpenAI — متعدد الوسائط"
    },
    {
        "name": "GPT-4o Mini 💡",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini", "fmt": "openai", "free": False, "requires_key": True,
        "description": "اقتصادي وذكي من OpenAI"
    },
    # --- Hugging Face (مجاني) ---
    {
        "name": "Qwen2.5 72B 🌟 (مجاني)",
        "url": "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct",
        "model": "Qwen/Qwen2.5-72B-Instruct", "fmt": "huggingface", "free": True, "requires_key": True,
        "description": "نموذج Qwen الضخم — مجاني عبر HuggingFace"
    },
    {
        "name": "Mistral 7B 🌊 (مجاني)",
        "url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
        "model": "mistralai/Mistral-7B-Instruct-v0.3", "fmt": "huggingface", "free": True, "requires_key": True,
        "description": "Mistral الموثوق — مجاني عبر HuggingFace"
    },
    # --- مخصص ---
    {
        "name": "⚙️ مخصص (Custom API)",
        "url": "", "model": "", "fmt": "openai", "free": False, "requires_key": True,
        "description": "اتصل بأي API متوافق مع OpenAI"
    },
]

# بناء القاموس الرئيسي
PRESETS: Dict[str, AIPreset] = {
    p["name"]: AIPreset(**{k: v for k, v in p.items() if k != "name"}, name=p["name"])
    for p in _PRESETS_RAW
}


# ============================================================
# طبقة الاتصال الأساسية (HTTP Layer)
# ============================================================
def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> dict:
    """إرسال طلب POST بصيغة JSON مع معالجة الأخطاء الكاملة."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        # محاولة فك ترميز JSON للخطأ إذا كان متاحاً
        try:
            err_json = json.loads(body)
            error_msg = json.dumps(err_json, ensure_ascii=False, indent=2)
        except:
            error_msg = body[:1000]
            
        raise RuntimeError(f"خطأ HTTP {e.code} من الخادم:\n{error_msg}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URLError: {e.reason}")
    except TimeoutError:
        raise RuntimeError("انتهت مهلة الاتصال (Timeout). تحقق من اتصالك بالإنترنت.")


# ============================================================
# محولات الصيغ (Format Adapters) — Factory Pattern
# ============================================================
def _build_gemini_payload(prompt: str, history: List[Dict], system: str, preset: AIPreset) -> tuple:
    """بناء طلب Gemini API."""
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
    """بناء طلب Anthropic Claude API."""
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
    """بناء طلب OpenAI-compatible API."""
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
    """بناء طلب HuggingFace Inference API."""
    # صيغة ChatML
    full_prompt = f"<|im_start|>system\n{system}<|im_end|>\n"
    for m in history[-6:]:  # آخر 6 رسائل فقط لتجنب تجاوز الحد
        role = "assistant" if m["role"] == "assistant" else "user"
        full_prompt += f"<|im_start|>{role}\n{m['content']}<|im_end|>\n"
    full_prompt += f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": min(preset.max_tokens, 1024),
            "temperature": preset.temperature,
            "return_full_text": False,
            "do_sample": True,
        }
    }
    return payload, {}


# ============================================================
# محلل الاستجابات (Response Parsers)
# ============================================================
def _parse_gemini(resp: dict) -> str:
    return resp["candidates"][0]["content"]["parts"][0]["text"]


def _parse_anthropic(resp: dict) -> str:
    return resp["content"][0]["text"]


def _parse_openai(resp: dict) -> str:
    return resp["choices"][0]["message"]["content"]


def _parse_huggingface(resp) -> str:
    if isinstance(resp, list) and resp:
        text = resp[0].get("generated_text", "")
        # إزالة الـ prompt من الاستجابة إذا عاد كاملاً
        if "<|im_start|>assistant" in text:
            text = text.split("<|im_start|>assistant")[-1].strip()
        return text
    return str(resp)


# ============================================================
# الدالة الرئيسية للاتصال بالذكاء الاصطناعي
# ============================================================
def call_ai(
    prompt: str,
    history: List[Dict],
    system: str,
    preset_name: str,
    api_key: str,
    custom_url: str = "",
    custom_model: str = "",
    custom_fmt: str = "openai"
) -> str:
    """
    الدالة الرئيسية للاتصال بأي نموذج ذكاء اصطناعي.
    
    Args:
        prompt: رسالة المستخدم الحالية
        history: سجل المحادثة السابقة
        system: تعليمات النظام (System Prompt)
        preset_name: اسم النموذج المختار
        api_key: مفتاح API
        custom_url: رابط API مخصص (للنموذج المخصص فقط)
        custom_model: اسم نموذج مخصص
        custom_fmt: صيغة API مخصصة
    
    Returns:
        نص الرد من النموذج
    """
    # جلب إعدادات النموذج
    preset = PRESETS.get(preset_name)
    
    if preset_name == "⚙️ مخصص (Custom API)":
        preset = AIPreset(
            name="مخصص", url=custom_url, model=custom_model,
            fmt=custom_fmt, free=False, requires_key=True
        )

    if not preset:
        return f"❌ النموذج '{preset_name}' غير موجود. اختر نموذجاً من القائمة."

    # التحقق من المفتاح
    if not api_key.strip() and preset.requires_key:
        return "❌ لم يتم إدخال مفتاح API. أدخله من زر الإعدادات (⚙️)."
    
    if not preset.url:
        return "❌ لم يتم تحديد رابط API. راجع الإعدادات."

    # تنظيف السجل
    clean_history = [
        {"role": m["role"], "content": str(m.get("content", ""))}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    try:
        # اختيار المحوّل المناسب
        fmt = preset.fmt
        builders = {
            "gemini": _build_gemini_payload,
            "anthropic": _build_anthropic_payload,
            "openai": _build_openai_payload,
            "huggingface": _build_huggingface_payload,
        }
        parsers = {
            "gemini": _parse_gemini,
            "anthropic": _parse_anthropic,
            "openai": _parse_openai,
            "huggingface": _parse_huggingface,
        }

        builder = builders.get(fmt, _build_openai_payload)
        parser = parsers.get(fmt, _parse_openai)

        payload, extra_headers = builder(prompt, clean_history, system, preset)

        # بناء الترويسات
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        if fmt == "gemini":
            url = f"{preset.url}?key={api_key}"
        elif fmt == "anthropic":
            headers.update({
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            })
            url = preset.url
        elif fmt == "huggingface":
            headers["Authorization"] = f"Bearer {api_key}"
            url = preset.url
        else:  # openai-compatible
            headers["Authorization"] = f"Bearer {api_key}"
            url = preset.url

        headers.update(extra_headers)

        logger.info(f"Calling AI: {preset_name} | fmt={fmt}")
        resp = _post_json(url, payload, headers)
        result = parser(resp)
        
        if not result or not result.strip():
            return "⚠️ الرد فارغ من النموذج. حاول مرة أخرى."
        
        return result.strip()

    except RuntimeError as e:
        err = str(e)
        logger.error(f"AI call error: {err}")
        # إظهار الخطأ الخام الحقيقي للمستخدم لضمان الشفافية والتشخيص الصحيح
        return f"❌ خطأ من الخادم (API Error):\n{err}"
    except KeyError as e:
        logger.error(f"Parse error: missing key {e}")
        return f"❌ خطأ في معالجة البيانات: المفتاح {e} مفقود في استجابة الخادم."
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ خطأ تقني غير متوقع:\n{str(e)}"


# ============================================================
# دوال مساعدة (Helper Functions)
# ============================================================
def get_preset_info(preset_name: str) -> Dict:
    """جلب معلومات نموذج معين."""
    preset = PRESETS.get(preset_name)
    if not preset:
        return {"name": preset_name, "url": "", "model": "", "fmt": "openai",
                "free": False, "requires_key": True, "description": ""}
    return {
        "name": preset.name,
        "url": preset.url,
        "model": preset.model,
        "fmt": preset.fmt,
        "free": preset.free,
        "requires_key": preset.requires_key,
        "description": preset.description,
    }


def get_free_models() -> List[Dict]:
    """جلب قائمة النماذج المجانية."""
    return [get_preset_info(name) for name, p in PRESETS.items() if p.free]


def get_paid_models() -> List[Dict]:
    """جلب قائمة النماذج المدفوعة."""
    return [get_preset_info(name) for name, p in PRESETS.items() if not p.free]


def get_all_models_grouped() -> Dict[str, List[Dict]]:
    """جلب جميع النماذج مجمعة حسب المزود."""
    groups: Dict[str, List] = {}
    for name, p in PRESETS.items():
        provider = name.split()[0] if name else "أخرى"
        if "Gemini" in name:
            provider = "Google Gemini"
        elif "Groq" in name:
            provider = "Groq (مجاني)"
        elif "Claude" in name:
            provider = "Anthropic Claude"
        elif "GPT" in name:
            provider = "OpenAI"
        elif "Qwen" in name or "Mistral" in name or "Llama" in name:
            provider = "HuggingFace (مجاني)"
        else:
            provider = "مخصص"
        groups.setdefault(provider, []).append(get_preset_info(name))
    return groups


def preset_names() -> List[str]:
    """قائمة بأسماء جميع النماذج."""
    return list(PRESETS.keys())


def test_connection(preset_name: str, api_key: str, custom_url: str = "", custom_model: str = "", custom_fmt: str = "openai") -> tuple[bool, str]:
    """
    اختبار الاتصال الفعلي بـ API.
    يعيد: (bool: نجاح/فشل, str: رسالة توضيحية)
    """
    if not api_key.strip() and PRESETS.get(preset_name) and PRESETS[preset_name].requires_key:
        return False, "❌ مفتاح API مفقود."

    try:
        # إرسال طلب بسيط جداً للتحقق
        test_prompt = "ping"
        # إرسال الطلب
        response = call_ai(
            prompt=test_prompt, 
            history=[], 
            system="respond with 'pong'", 
            preset_name=preset_name, 
            api_key=api_key,
            custom_url=custom_url,
            custom_model=custom_model,
            custom_fmt=custom_fmt
        )

        if "❌" in response or "⏳" in response or "🔑" in response or "🔗" in response:
            return False, response
        
        return True, "✅ تم الاتصال بنجاح! الخادم يستجيب."
    except Exception as e:
        return False, f"❌ فشل الاتصال: {str(e)}"
