# -*- coding: utf-8 -*-
"""
Fuhrer - Saudi Labor Law Assistant
"""

import os
import streamlit as st
from dotenv import load_dotenv
from legal_tools import get_tools_for_persona, PERSONA_PROMPTS
from legal_database import get_legal_database
from ai_engine import HuggingFaceEngine, GroqEngine
from storage import SupabaseStorage

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Fuhrer | قانون العمل السعودي",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
st.sidebar.title("⚙️ إعدادات API")
hf_token = st.sidebar.text_input("Hugging Face Token", type="password", value=os.getenv("HUGGINGFACE_TOKEN", ""))
groq_token = st.sidebar.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
supabase_url = st.sidebar.text_input("Supabase URL", value=os.getenv("SUPABASE_URL", ""))
supabase_key = st.sidebar.text_input("Supabase Key", type="password", value=os.getenv("SUPABASE_KEY", ""))

if st.sidebar.button("اختبار الاتصال"):
    with st.spinner("جاري الاختبار..."):
        if hf_token:
            try:
                hf = HuggingFaceEngine(api_token=hf_token)
                hf.generate("اختبار", max_tokens=5)
                st.sidebar.success("✅ Hugging Face متصل")
            except:
                st.sidebar.error("❌ Hugging Face خطأ")
        else:
            st.sidebar.warning("⚠️ Hugging Face Token مفقود")

        if groq_token:
            try:
                groq = GroqEngine(api_key=groq_token)
                groq.generate("اختبار", max_tokens=5)
                st.sidebar.success("✅ Groq متصل")
            except:
                st.sidebar.error("❌ Groq خطأ")
        else:
            st.sidebar.warning("⚠️ Groq API Key مفقود")

        if supabase_url and supabase_key:
            try:
                supabase = SupabaseStorage(url=supabase_url, key=supabase_key)
                supabase.list_files()
                st.sidebar.success("✅ Supabase متصل")
            except:
                st.sidebar.error("❌ Supabase خطأ")
        else:
            st.sidebar.warning("⚠️ Supabase URL/Key مفقود")

# Header
st.title("⚖️ Fuhrer - قانون العمل السعودي")
st.markdown("مساعد قانوني ذكي لنظام العمل السعودي")

# Persona selection
st.markdown("## اختر دورك")
persona = None
cols = st.columns(4)
for idx, (pid, pname) in enumerate(["worker", "employer", "lawyer", "judge"]):
    with cols[idx]:
        if st.button(f"{pname}", use_container_width=True):
            persona = pid
            st.session_state.persona = pid

if "persona" in st.session_state:
    persona = st.session_state.persona

if not persona:
    st.warning("يرجى اختيار دورك أولاً")
    st.stop()

# Tools
tools_list = get_tools_for_persona(persona)
st.markdown("## الأدوات المتاحة")
cols = st.columns(3)
for i, tool in enumerate(tools_list):
    with cols[i % 3]:
        if st.button(f"{tool['icon']} {tool['name']}", use_container_width=True):
            st.session_state.selected_tool = tool["func"]

# Features
with st.expander("🔍 بحث قانوني"):
    query = st.text_input("ادخل كلمات البحث:")
    if query:
        db = get_legal_database()
        results = db.search_articles(query, limit=10)
        for result in results:
            with st.expander(f"المادة {result['id']}: {result['title']}"):
                st.write(f"**الفئة:** {result['category']}")
                st.write(f"**المحتوى:** {result['content']}")

with st.expander("💰 حساب نهاية الخدمة"):
    col1, col2, col3 = st.columns(3)
    with col1: years = st.number_input("سنوات العمل:", min_value=0.0, value=5.0)
    with col2: salary = st.number_input("آخر راتب (ريال):", min_value=0, value=10000)
    with col3: reason = st.selectbox("سبب الانتهاء:", ["استقالة", "فصل تعسفي", "تقاعد"])
    if st.button("احسب"):
        from legal_tools import calculate_end_of_service
        result = calculate_end_of_service(years, salary, reason)
        if "error" not in result:
            st.success(f"مستحقاتك: {result['benefit_amount']:,} ريال")
        else:
            st.error(result["error"])

with st.expander("🤖 مساعد قانوني"):
    if st.session_state.get("api_status", {}).get("Groq") != "✅ متصل":
        st.warning("قم بتوصيل API أولاً")
    else:
        query = st.text_area("اسأل عن أي مسألة قانونية:")
        if query and st.button("ارسال"):
            with st.spinner("جاري التفكير..."):
                ai = GroqEngine(api_key=groq_token)
                prompt = f"{PERSONA_PROMPTS[persona]}\n\nسؤال: {query}"
                response = ai.generate(prompt, max_tokens=1000)
                st.markdown("### الإجابة")
                st.write(response)