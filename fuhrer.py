# -*- coding: utf-8 -*-
"""
Fuhrer - Saudi Labor Law Assistant
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ======================
# STYLES (تصميم أصلي + تحسينات طفيفة)
# ======================
def get_custom_styles():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
        
        /* Global RTL & Font */
        html, body, [class*="css"] {
            font-family: 'Cairo', sans-serif !important;
            direction: rtl !important;
            text-align: right !important;
        }
        
        /* Main container */
        .main > div {
            max-width: 1000px !important;
            padding: 1rem !important;
        }
        
        /* Sidebar */
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e3a8a 0%, #0f172a 100%) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.5rem !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            background-color: #f9fafb !important;
        }
        
        /* File uploader */
        .stFileUploader > div {
            border: 2px dashed #3b82f6 !important;
            border-radius: 12px !important;
            padding: 2rem !important;
            background-color: #f0f9ff !important;
        }
        
        /* Cards */
        .stCard, [data-testid="stExpander"] {
            background: white !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px !important;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0 !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
            color: white !important;
        }
        
        /* Persona buttons (تصميم أنيق) */
        .persona-button {
            background: white !important;
            border: 2px solid #3b82f6 !important;
            color: #1e40af !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            transition: all 0.3s ease !important;
            text-align: center !important;
            cursor: pointer !important;
        }
        .persona-button:hover {
            background: #3b82f6 !important;
            color: white !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }
        
        /* Alerts */
        .stAlert {
            border-radius: 8px !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
            color: white !important;
            padding: 2rem 1rem !important;
            border-radius: 0 0 15px 15px !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        }
    </style>
    """

st.markdown(get_custom_styles(), unsafe_allow_html=True)

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Fuhrer | قانون العمل السعودي",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# SIDEBAR - API Configuration
# ======================
def setup_sidebar():
    st.sidebar.markdown("## ⚙️ إعدادات API")
    st.sidebar.markdown("---")

    # API Keys Input
    api_config = {
        "HUGGINGFACE_TOKEN": st.sidebar.text_input("🤗 Hugging Face Token", type="password", value=os.getenv("HUGGINGFACE_TOKEN", "")),
        "GROQ_API_KEY": st.sidebar.text_input("⚡ Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", "")),
        "SUPABASE_URL": st.sidebar.text_input("🗄️ Supabase URL", value=os.getenv("SUPABASE_URL", "")),
        "SUPABASE_KEY": st.sidebar.text_input("🔑 Supabase Key", type="password", value=os.getenv("SUPABASE_KEY", ""))
    }

    # Test Connection Button
    if st.sidebar.button("🔍 اختبار الاتصال", use_container_width=True):
        with st.spinner("جاري الاختبار..."):
            test_connections(api_config)

    # Display status
    display_connection_status()

    return api_config

def test_connections(api_config):
    results = {}

    # Test Hugging Face
    if api_config["HUGGINGFACE_TOKEN"]:
        try:
            from ai_engine import HuggingFaceEngine
            hf = HuggingFaceEngine(api_token=api_config["HUGGINGFACE_TOKEN"])
            hf.generate("اختبار", max_tokens=5)
            results["Hugging Face"] = {"status": "✅ متصل", "color": "green"}
        except Exception as e:
            results["Hugging Face"] = {"status": f"❌ خطأ", "color": "red", "error": str(e)}
    else:
        results["Hugging Face"] = {"status": "⚠️ مفقود", "color": "orange"}

    # Test Groq
    if api_config["GROQ_API_KEY"]:
        try:
            from ai_engine import GroqEngine
            groq = GroqEngine(api_key=api_config["GROQ_API_KEY"])
            groq.generate("اختبار", max_tokens=5)
            results["Groq"] = {"status": "✅ متصل", "color": "green"}
        except Exception as e:
            results["Groq"] = {"status": f"❌ خطأ", "color": "red", "error": str(e)}
    else:
        results["Groq"] = {"status": "⚠️ مفقود", "color": "orange"}

    # Test Supabase
    if api_config["SUPABASE_URL"] and api_config["SUPABASE_KEY"]:
        try:
            from storage import SupabaseStorage
            supabase = SupabaseStorage(url=api_config["SUPABASE_URL"], key=api_config["SUPABASE_KEY"])
            supabase.list_files()
            results["Supabase"] = {"status": "✅ متصل", "color": "green"}
        except Exception as e:
            results["Supabase"] = {"status": f"❌ خطأ", "color": "red", "error": str(e)}
    else:
        results["Supabase"] = {"status": "⚠️ مفقود", "color": "orange"}

    st.session_state.api_status = results

def display_connection_status():
    if "api_status" in st.session_state:
        st.sidebar.markdown("### 📡 حالة الاتصال")
        for service, result in st.session_state.api_status.items():
            st.sidebar.markdown(f"**{service}**: <span style='color:{result['color']}'>{result['status']}</span>", unsafe_allow_html=True)
            if result.get("error") and st.sidebar.button(f"🔴 تفاصيل {service}", key=f"err_{service}"):
                st.sidebar.error(result["error"])

# ======================
# PERSONA SELECTION (تصميم أنيق)
# ======================
PERSONA_INFO = {
    "worker": {"name": "عامل", "icon": "👷", "description": "للموظفين والعاملين", "color": "#10b981"},
    "employer": {"name": "صاحب عمل", "icon": "🏢", "description": "لأصحاب العمل", "color": "#3b82f6"},
    "lawyer": {"name": "محامي", "icon": "⚖️", "description": " للمحامين", "color": "#ef4444"},
    "judge": {"name": "قاضي", "icon": "👨⚖️", "description": " للقضاة", "color": "#8b5cf6"}
}

def select_persona():
    st.markdown("<div class='header'><h1>⚖️ Fuhrer - قانون العمل السعودي</h1><p>مساعد قانوني ذكي لنظام العمل السعودي</p></div>", unsafe_allow_html=True)
    st.markdown("## 👤 اختر دورك")
    
    cols = st.columns(4)
    selected_persona = None
    
    for idx, (persona_id, info) in enumerate(PERSONA_INFO.items()):
        with cols[idx]:
            button_html = f"""
            <div class="persona-button" onclick="this.parentElement.querySelector('button').click()">
                <div style="font-size: 2rem;">{info['icon']}</div>
                <div style="font-weight: bold; margin-top: 0.5rem;">{info['name']}</div>
                <div style="font-size: 0.8rem; color: #6b7280; margin-top: 0.5rem;">{info['description']}</div>
            </div>
            """
            st.markdown(button_html, unsafe_allow_html=True)
            if st.button("", key=f"persona_{persona_id}"):
                selected_persona = persona_id
                st.session_state.persona = persona_id
    
    if "persona" in st.session_state:
        selected_persona = st.session_state.persona
    
    return selected_persona

# ======================
# MAIN APP
# ======================
def main():
    api_config = setup_sidebar()
    for key, value in api_config.items():
        os.environ[key] = value

    persona = select_persona()
    if not persona:
        st.warning("⚠️ يرجى اختيار دورك أولاً")
        st.stop()

    persona_info = PERSONA_INFO[persona]

    # ======================
    # TOOLS & FEATURES
    # ======================
    st.markdown("---")
    st.markdown(f"### 🛠️ أدوات {persona_info['name']}")

    # Get tools for persona
    try:
        from legal_tools import get_tools_for_persona, PERSONA_PROMPTS
        tools_list = get_tools_for_persona(persona)
        system_prompt = PERSONA_PROMPTS.get(persona, "")
    except Exception as e:
        st.error(f"خطأ في تحميل الأدوات: {str(e)}")
        st.stop()

    # Display tools in a clean grid
    cols = st.columns(3)
    for i, tool in enumerate(tools_list):
        with cols[i % 3]:
            if st.button(f"{tool['icon']} {tool['name']}", use_container_width=True, key=f"tool_{tool['func']}"):
                st.session_state.selected_tool = tool["func"]
                st.rerun()

    # ======================
    # FEATURES SECTIONS
    # ======================
    st.markdown("---")

    # 1. Legal Search
    with st.expander("🔍 بحث قانوني", expanded=False):
        query = st.text_input("ادخل كلمات البحث:")
        if query:
            try:
                from legal_database import get_legal_database
                db = get_legal_database()
                results = db.search_articles(query, limit=10)
                if results:
                    for result in results:
                        with st.expander(f"📄 المادة {result['id']}: {result['title']}"):
                            st.markdown(f"**الفئة:** {result['category']}")
                            st.markdown(f"**المحتوى:** {result['content']}")
                else:
                    st.info("لا يوجد نتائج")
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

    # 2. Document Analysis
    with st.expander("📄 تحليل مستندات", expanded=False):
        uploaded = st.file_uploader("رفع ملف (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"])
        if uploaded:
            try:
                from file_processing import process_uploaded_file
                text = process_uploaded_file(uploaded)
                st.success("✅ تم استخراج النص!")
                st.text_area("النص:", text[:2000], height=200)
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

    # 3. End of Service Calculation
    with st.expander("💰 حساب نهاية الخدمة", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1: years = st.number_input("سنوات العمل:", min_value=0.0, value=5.0, step=0.5)
        with col2: salary = st.number_input("آخر راتب (ريال):", min_value=0, value=10000, step=1000)
        with col3: reason = st.selectbox("سبب الانتهاء:", ["استقالة", "فصل تعسفي", "تقاعد"])
        
        if st.button("📊 احسب"):
            try:
                from legal_tools import calculate_end_of_service
                result = calculate_end_of_service(years, salary, reason)
                if "error" not in result:
                    st.success(f"مستحقاتك: **{result['benefit_amount']:,} ريال** ({result['benefit_days']} يوم)")
                else:
                    st.error(result["error"])
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

    # 4. AI Assistant
    with st.expander("🤖 مساعد قانوني ذكي", expanded=True):
        if st.session_state.get("api_status", {}).get("Groq", {}).get("status") != "✅ متصل":
            st.warning("⚠️ قم بتوصيل API أولاً (Groq أو Hugging Face)")
        else:
            query = st.text_area("اسأل عن أي مسألة قانونية:")
            if query and st.button("💬 ارسال"):
                with st.spinner("جاري التفكير..."):
                    try:
                        from ai_engine import get_ai_engine
                        ai = get_ai_engine("groq")
                        prompt = f"{system_prompt}\n\nسؤال المستخدم: {query}\n\nأجب بإيجاز ووضوح، مستنداً إلى نظام العمل السعودي."
                        response = ai.generate(prompt, max_tokens=1000)
                        st.markdown("### 💡 الإجابة")
                        st.markdown(response)
                    except Exception as e:
                        st.error(f"خطأ: {str(e)}")

if __name__ == "__main__":
    main()