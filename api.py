import os
from typing import List
from dotenv import load_dotenv
load_dotenv()

import ai_engine


def ai_call(prompt: str, history: List[dict] = None, system: str = "", preset_name: str = None, api_key: str = None, custom_url: str = "", custom_model: str = "", custom_fmt: str = "openai") -> str:
    """واجهة بسيطة لاستدعاء محرك الذكاء الاصطناعي دون تبعية لـ Streamlit.
    تستعمل المتغيرات البيئية كقيمة افتراضية إن لم تُمرّر معلمات.
    """
    if history is None:
        history = []

    preset_name = preset_name or os.environ.get('PRESET_NAME', 'Führer Law Brain (Qwen 0.6B) 🧠')
    api_key = api_key or os.environ.get('API_KEY', '')
    custom_url = custom_url or os.environ.get('CUSTOM_URL', '')
    custom_model = custom_model or os.environ.get('CUSTOM_MODEL', '')
    custom_fmt = custom_fmt or os.environ.get('CUSTOM_FMT', 'openai')

    return ai_engine.call_ai(
        prompt=prompt,
        history=history,
        system=system,
        preset_name=preset_name,
        api_key=api_key,
        custom_url=custom_url,
        custom_model=custom_model,
        custom_fmt=custom_fmt,
    )
