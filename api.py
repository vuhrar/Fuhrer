"""
api.py — جسر الاستدعاء الموحّد بين واجهة المستخدم ومحرك الذكاء الاصطناعي.
لا يحتوي على أي بيانات وهمية أو CSV أو نماذج محلية.
"""

import streamlit as st
import ai_engine


def ai_call(prompt: str, history: list = None, system: str = "") -> str:
    """
    استدعاء الذكاء الاصطناعي باستخدام الإعدادات الحالية في session_state.

    المعاملات:
        prompt  : نص الطلب
        history : سجل المحادثة السابقة (قائمة من dict role/content)
        system  : تعليمات النظام (يُستخدم preset_name إن لم يُحدَّد)

    العائد:
        نص الرد من نموذج الذكاء الاصطناعي، أو رسالة خطأ واضحة.
    """
    if history is None:
        history = []

    preset_name = st.session_state.get("preset_name", "groq_llama")
    api_key     = st.session_state.get("api_key", "")

    if not api_key:
        return "⚠️ لم يتم إدخال مفتاح API. افتح الإعدادات (⚙️) وأدخل المفتاح أولاً."

    try:
        return ai_engine.call_ai(
            prompt=prompt,
            history=history,
            system=system,
            preset_name=preset_name,
            api_key=api_key,
        )
    except Exception as e:
        return f"❌ خطأ في استدعاء الذكاء الاصطناعي: {e}"
