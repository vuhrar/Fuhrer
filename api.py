import streamlit as st
import ai_engine


def ai_call(prompt: str, history: list = None, system: str = "") -> str:
    if history is None:
        history = []

    preset_name = st.session_state.get("preset_name", "Groq LLaMA 3.3 70B 🚀 (مجاني)")
    api_key     = st.session_state.get("api_key", "")
    custom_url  = st.session_state.get("custom_url", "")
    custom_model = st.session_state.get("custom_model", "")
    custom_fmt   = st.session_state.get("custom_fmt", "openai")

    if not api_key:
        return "⚠️ لم يتم إدخال مفتاح API. افتح الإعدادات (⚙️) وأدخل المفتاح أولاً."

    try:
        return ai_engine.call_ai(
            prompt=prompt,
            history=history,
            system=system,
            preset_name=preset_name,
            api_key=api_key,
            custom_url=custom_url,
            custom_model=custom_model,
            custom_fmt=custom_fmt
        )
    except Exception as e:
        return f"❌ خطأ في استدعاء الذكاء الاصطناعي: {e}"
