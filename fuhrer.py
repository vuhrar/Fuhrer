# -*- coding: utf-8 -*-
"""
Fuhrer - Saudi Labor Law Assistant
A comprehensive Streamlit app for Saudi labor law analysis, document generation, and AI-powered legal tools.
"""

# ======================
# IMPORTS
# ======================
import os
import sys
import json
import time
import base64
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# ======================
# CUSTOM STYLES (from styles.py)
# ======================
def get_custom_styles():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Cairo', 'Amiri', sans-serif !important; direction: rtl !important; text-align: right !important; }
        .main > div { max-width: 1200px !important; padding: 1rem !important; }
        .stButton > button {
            background: linear-gradient(135deg, #0066cc 0%, #004080 100%) !important;
            color: white !important; border: none !important; border-radius: 8px !important;
            padding: 0.75rem 2rem !important; font-size: 1.1rem !important; font-weight: 600 !important;
        }
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            border: 2px solid #e0e0e0 !important; border-radius: 8px !important;
            background-color: #f8f9fa !important;
        }
        .stFileUploader > div { border: 2px dashed #0066cc !important; border-radius: 12px !important; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0066cc 0%, #004080 100%) !important; color: white !important; }
        .stAlert { border-radius: 8px !important; }
        div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0066cc 0%, #004080 100%) !important; }
    </style>
    """

# Inject custom styles
st.markdown(get_custom_styles(), unsafe_allow_html=True)

# ======================
# PAGE CONFIGURATION
# ======================
st.set_page_config(
    page_title="Fuhrer | قانون العمل السعودي",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# SIDEBAR - API Configuration & Status
# ======================
def setup_sidebar():
    """Configure sidebar with API settings and connection status"""

    st.sidebar.markdown("## ⚙️ **إعدادات API**")
    st.sidebar.markdown("---")

    # API Keys Input (with password masking)
    api_config = {
        "HUGGINGFACE_TOKEN": st.sidebar.text_input(
            "🤗 Hugging Face Token",
            type="password",
            value=os.getenv("HUGGINGFACE_TOKEN", ""),
            key="hf_token"
        ),
        "GROQ_API_KEY": st.sidebar.text_input(
            "⚡ Groq API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            key="groq_token"
        ),
        "SUPABASE_URL": st.sidebar.text_input(
            "🗄️ Supabase URL",
            value=os.getenv("SUPABASE_URL", ""),
            key="supabase_url"
        ),
        "SUPABASE_KEY": st.sidebar.text_input(
            "🔑 Supabase Key",
            type="password",
            value=os.getenv("SUPABASE_KEY", ""),
            key="supabase_key"
        )
    }

    # Connection Test Button
    if st.sidebar.button("🔍 **اختبار الاتصال**", use_container_width=True, key="test_connection"):
        with st.spinner("جاري اختبار اتصالات API..."):
            test_connections(api_config)

    # Display connection status
    display_connection_status()

    return api_config

def test_connections(api_config: Dict):
    """Test all API connections and store results in session state"""
    results = {}

    # Test Hugging Face
    if api_config["HUGGINGFACE_TOKEN"]:
        try:
            from ai_engine import HuggingFaceEngine
            hf = HuggingFaceEngine(api_token=api_config["HUGGINGFACE_TOKEN"])
            test_response = hf.generate("اختبار الاتصال", max_tokens=5)
            results["Hugging Face"] = {"status": "✅ متصل", "color": "green", "error": None}
        except Exception as e:
            results["Hugging Face"] = {"status": f"❌ خطأ", "color": "red", "error": str(e)}
    else:
        results["Hugging Face"] = {"status": "⚠️ مفقود", "color": "orange", "error": "API Key مفقود"}

    # Test Groq
    if api_config["GROQ_API_KEY"]:
        try:
            from ai_engine import GroqEngine
            groq = GroqEngine(api_key=api_config["GROQ_API_KEY"])
            test_response = groq.generate("اختبار الاتصال", max_tokens=5)
            results["Groq"] = {"status": "✅ متصل", "color": "green", "error": None}
        except Exception as e:
            results["Groq"] = {"status": f"❌ خطأ", "color": "red", "error": str(e)}
    else:
        results["Groq"] = {"status": "⚠️ مفقود", "color": "orange", "error": "API Key مفقود"}

    # Test Supabase
    if api_config["SUPABASE_URL"] and api_config["SUPABASE_KEY"]:
        try:
            from storage import SupabaseStorage
            supabase = SupabaseStorage(
                url=api_config["SUPABASE_URL"],
                key=api_config["SUPABASE_KEY"]
            )
            test_files = supabase.list_files()
            results["Supabase"] = {"status": "✅ متصل", "color": "green", "error": None}
        except Exception as e:
            results["Supabase"] = {"status": f"❌ خطأ", "color": "red", "error": str(e)}
    else:
        results["Supabase"] = {"status": "⚠️ مفقود", "color": "orange", "error": "URL/Key مفقود"}

    # Store results in session state
    st.session_state.api_status = results

def display_connection_status():
    """Display API connection status in sidebar"""
    if "api_status" in st.session_state:
        st.sidebar.markdown("### 📡 **حالة الاتصال**")
        for service, result in st.session_state.api_status.items():
            status_html = f"""
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span>{result['status']}</span>
            </div>
            """
            st.sidebar.markdown(f"**{service}**:", unsafe_allow_html=True)
            st.sidebar.markdown(status_html, unsafe_allow_html=True)
            if result["error"] and st.sidebar.button(f"🔴 تفاصيل", key=f"err_{service}"):
                st.sidebar.error(result["error"])

# ======================
# PERSONA SYSTEM
# ======================
PERSONA_INFO = {
    "worker": {
        "name": "عامل",
        "icon": "👷",
        "description": "للموظفين والعاملين الذين يريدون معرفة حقوقهم",
        "color": "#28a745"
    },
    "employer": {
        "name": "صاحب عمل",
        "icon": "🏢",
        "description": "لأصحاب العمل لإدارة عقودهم والتزاماتهم القانونية",
        "color": "#0066cc"
    },
    "lawyer": {
        "name": "محامي",
        "icon": "⚖️",
        "description": " للمحامين المتخصصين في قانون العمل",
        "color": "#dc3545"
    },
    "judge": {
        "name": "قاضي",
        "icon": "👨⚖️",
        "description": " للقضاة وذوي الاختصاص القانوني",
        "color": "#6f42c1"
    }
}

def select_persona():
    """Let user select persona and return it"""
    st.markdown("## 👤 **اختر دورك**")
    cols = st.columns(4)
    selected_persona = None

    for idx, (persona_id, info) in enumerate(PERSONA_INFO.items()):
        with cols[idx % 4]:
            if st.button(
                f"{info['icon']} {info['name']}",
                use_container_width=True,
                key=f"persona_{persona_id}"
            ):
                selected_persona = persona_id
                st.session_state.persona = persona_id

    # If persona already selected, use it
    if "persona" in st.session_state:
        selected_persona = st.session_state.persona
        st.markdown(f"### دورك الحالي: {PERSONA_INFO[selected_persona]['icon']} {PERSONA_INFO[selected_persona]['name']}")

    return selected_persona

# ======================
# MAIN APP
# ======================
def main():
    """Main application function"""

    # Setup sidebar
    api_config = setup_sidebar()

    # Update environment variables from sidebar inputs
    for key, value in api_config.items():
        os.environ[key] = value

    # Select persona
    persona = select_persona()
    if not persona:
        st.warning("⚠️ **يرجى اختيار دورك أولاً** (عامل، صاحب عمل، محامي، قاضي)")
        st.stop()

    # Get tools for selected persona
    try:
        from legal_tools import get_tools_for_persona, PERSONA_PROMPTS
        tools_list = get_tools_for_persona(persona)
        system_prompt = PERSONA_PROMPTS.get(persona, "")
    except Exception as e:
        st.error(f"❌ خطأ في تحميل الأدوات: {str(e)}")
        st.stop()

    # Display persona-specific welcome message
    persona_info = PERSONA_INFO[persona]
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {persona_info['color']}22 0%, {persona_info['color']}44 100%);
                padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;'>
        <h1 style='color: {persona_info['color']}; margin: 0;'>{persona_info['icon']} مرحباً، {persona_info['name']}!</h1>
        <p style='margin: 0.5rem 0 0 0; color: #666;'>{persona_info['description']}</p>
    </div>
    """, unsafe_allow_html=True)

    # ======================
    # MAIN FEATURES
    # ======================

    # 1. Legal Search
    with st.expander("🔍 **بحث قانوني**", expanded=False):
        search_query = st.text_input("ادخل كلمات البحث:", key="search_query")
        if search_query:
            try:
                from legal_database import get_legal_database
                db = get_legal_database()
                results = db.search_articles(search_query, limit=10)
                if results:
                    st.markdown("### 📚 **نتائج البحث**")
                    for result in results:
                        with st.expander(f"📄 **المادة {result['id']}: {result['title']}"):
                            st.markdown(f"**الفئة:** {result['category']}")
                            st.markdown(f"**المحتوى:** {result['content']}")
                            if result.get("tags"):
                                st.markdown(f"**العلامات:** {', '.join(result['tags'])}")
                else:
                    st.info("لا يوجد نتائج لهذا البحث.")
            except Exception as e:
                st.error(f"❌ خطأ في البحث: {str(e)}")

    # 2. Document Analysis
    with st.expander("📄 **تحليل مستندات**", expanded=False):
        uploaded_file = st.file_uploader("رفع ملف (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"], key="doc_upload")
        if uploaded_file:
            try:
                from file_processing import process_uploaded_file
                text = process_uploaded_file(uploaded_file)
                st.success("✅ تم استخراج النص بنجاح!")
                st.text_area("النص المستخرج:", text[:2000], height=200, key="extracted_text")

                # Auto-analyze with AI
                if st.button("🔍 تحليل تلقائي", key="auto_analyze"):
                    with st.spinner("جاري التحليل..."):
                        try:
                            from ai_engine import get_ai_engine
                            ai = get_ai_engine("groq")  # Use Groq for faster response
                            prompt = f"""
                            تحليل هذا النص حسب نظام العمل السعودي:
                            {text[:1000]}

                            قم بتحديد:
                            1. المواد القانونية ذات الصلة
                            2. أي مخالفات محتملة
                            3. حقوق والتزامات الطرفين
                            """
                            analysis = ai.generate(prompt, max_tokens=500)
                            st.markdown("### 📊 **تحليل المستند**")
                            st.markdown(analysis)
                        except Exception as e:
                            st.error(f"❌ خطأ في التحليل: {str(e)}")
            except Exception as e:
                st.error(f"❌ خطأ في معالجة الملف: {str(e)}")

    # 3. End of Service Calculation
    with st.expander("💰 **حساب نهاية الخدمة**", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            years = st.number_input("سنوات العمل:", min_value=0.0, value=5.0, step=0.5, key="yos_years")
        with col2:
            last_salary = st.number_input("آخر راتب (ريال):", min_value=0, value=10000, step=1000, key="yos_salary")
        with col3:
            reason = st.selectbox("سبب الانتهاء:", ["استقالة", "فصل تعسفي", "تقاعد", "انتهاء عقد"], key="yos_reason")

        if st.button("📊 احسب مستحقاتي", key="calculate_eos"):
            try:
                from legal_tools import calculate_end_of_service
                result = calculate_end_of_service(years, last_salary, reason)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("✅ **نتائج حساب نهاية الخدمة**")
                    st.markdown(f"""
                    - **مدة العمل:** {result['years']} سنوات
                    - **آخر راتب:** {result['last_salary']:,} ريال
                    - **سبب الانتهاء:** {result['reason']}
                    - **مستحقات:** {result['benefit_days']} يوم × ({result['last_salary']}/30) = **{result['benefit_amount']:,} ريال**
                    """)
            except Exception as e:
                st.error(f"❌ خطأ في الحساب: {str(e)}")

    # 4. AI Assistant
    with st.expander("🤖 **المساعد القانوني الذكي**", expanded=True):
        if st.session_state.get("api_status", {}).get("Groq", {}).get("status") != "✅ متصل" and \
           st.session_state.get("api_status", {}).get("Hugging Face", {}).get("status") != "✅ متصل":
            st.warning("⚠️ **قم بتوصيل API أولاً** (Groq أو Hugging Face) من sidebar")
        else:
            user_query = st.text_area(
                "اسأل عن أي مسألة قانونية مربوطة بنظام العمل السعودي:",
                height=150,
                key="ai_query"
            )

            if user_query and st.button("💬 ارسال", key="send_query"):
                with st.spinner("جاري التفكير..."):
                    try:
                        from ai_engine import get_ai_engine
                        ai = get_ai_engine("groq")  # Priority to Groq for speed

                        # Build persona-specific prompt
                        prompt = f"""
                        {system_prompt}

                        سؤال المستخدم: {user_query}

                        أجب بإيجاز ووضوح، مستنداً إلى نظام العمل السعودي.
                        """
                        response = ai.generate(prompt, max_tokens=1000)
                        st.markdown("### 💡 **الإجابة**")
                        st.markdown(response)
                    except Exception as e:
                        st.error(f"❌ خطأ في توليد الإجابة: {str(e)}")

    # 5. Tools Section
    if tools_list:
        st.markdown("## 🛠️ **الأدوات المتاحة**")
        cols = st.columns(3)
        for i, tool in enumerate(tools_list):
            with cols[i % 3]:
                if st.button(
                    f"{tool['icon']} {tool['name']}",
                    use_container_width=True,
                    key=f"tool_{tool['func']}"
                ):
                    st.session_state.selected_tool = tool["func"]
                    st.rerun()

# ======================
# RUN THE APP
# ======================
if __name__ == "__main__":
    main()