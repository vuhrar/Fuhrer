# -*- coding: utf-8 -*-
"""
Fuhrer - Saudi Labor Law Assistant | تصميم احترافي 8K
نسخة نهائية بدون أخطاء + ألوان صحيحة
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ======================
# PROFESSIONAL 8K STYLES (تصميم دقيق)
# ======================
def get_professional_styles():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

        /* ===== GLOBAL STYLES ===== */
        html, body, [class*="css"] {
            font-family: 'Cairo', sans-serif !important;
            direction: rtl !important;
            text-align: right !important;
            background-color: #111827 !important;
            color: #FFFFFF !important;
        }

        /* ===== MAIN CONTAINER ===== */
        .main > div {
            max-width: 1000px !important;
            padding: 2rem !important;
            background-color: #111827 !important;
        }

        /* ===== SIDEBAR ===== */
        div[data-testid="stSidebar"] {
            background-color: #1F2937 !important;
            border-right: 1px solid #D4AF37 !important;
        }

        /* ===== BUTTONS (بدون label_visibility) ===== */
        .stButton > button {
            background-color: #374151 !important;
            color: #FFFFFF !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 8px !important;
            padding: 0.75rem 2rem !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        .stButton > button:hover {
            background-color: #D4AF37 !important;
            color: #111827 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3) !important;
        }

        /* ===== INPUT FIELDS ===== */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #F9FAFB !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            color: #111827 !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #D4AF37 !important;
            box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1) !important;
        }

        /* ===== FILE UPLOADER ===== */
        .stFileUploader > div {
            background-color: #F9FAFB !important;
            border: 2px dashed #D4AF37 !important;
            border-radius: 12px !important;
            padding: 2rem !important;
            color: #111827 !important;
        }

        /* ===== EXPANDERS ===== */
        .stExpander {
            background-color: #1F2937 !important;
            border: 1px solid #374151 !important;
            border-radius: 12px !important;
            margin: 1rem 0 !important;
        }

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab"] {
            background-color: #374151 !important;
            color: #FFFFFF !important;
            border-radius: 8px 8px 0 0 !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #D4AF37 !important;
            color: #111827 !important;
        }

        /* ===== PERSONA BUTTONS (بدون أيموجي) ===== */
        .persona-container {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            justify-content: center;
            margin: 1.5rem 0;
        }
        .persona-button {
            background-color: #1F2937 !important;
            border: 2px solid #D4AF37 !important;
            color: #FFFFFF !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            width: 200px !important;
            text-align: center !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            font-weight: 600 !important;
        }
        .persona-button:hover {
            background-color: #D4AF37 !important;
            color: #111827 !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 8px 16px rgba(212, 175, 55, 0.3) !important;
        }

        /* ===== HEADER ===== */
        .header {
            background: linear-gradient(135deg, #1F2937 0%, #374151 100%) !important;
            color: #FFFFFF !important;
            padding: 2rem 1rem !important;
            border-radius: 0 0 15px 15px !important;
            margin-bottom: 2rem !important;
            border: 1px solid #D4AF37 !important;
        }
        .header h1 {
            margin: 0 !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
        }
        .header p {
            margin: 0.5rem 0 0 0 !important;
            opacity: 0.9 !important;
            font-size: 1.1rem !important;
        }

        /* ===== ALERTS ===== */
        .stAlert {
            background-color: #1F2937 !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
        }

        /* ===== TOOLS GRID ===== */
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }
        .tool-card {
            background-color: #1F2937 !important;
            border: 1px solid #374151 !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
        }
        .tool-card:hover {
            border-color: #D4AF37 !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 8px 16px rgba(212, 175, 55, 0.2) !important;
        }

        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-track {
            background: #1F2937;
        }
        ::-webkit-scrollbar-thumb {
            background: #374151;
            border-radius: 5px;
        }
    </style>
    """
st.markdown(get_professional_styles(), unsafe_allow_html=True)

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

    # API Keys Input (بدون label_visibility)
    hf_token = st.sidebar.text_input("🤗 Hugging Face Token", type="password", value=os.getenv("HUGGINGFACE_TOKEN", ""))
    groq_key = st.sidebar.text_input("⚡ Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
    supabase_url = st.sidebar.text_input("🗄️ Supabase URL", value=os.getenv("SUPABASE_URL", ""))
    supabase_key = st.sidebar.text_input("🔑 Supabase Key", type="password", value=os.getenv("SUPABASE_KEY", ""))

    # Test Connection Button
    if st.sidebar.button("🔍 اختبار الاتصال", use_container_width=True):
        with st.spinner("جاري الاختبار..."):
            test_connections(hf_token, groq_key, supabase_url, supabase_key)

    # Display connection status
    display_connection_status()
    return hf_token, groq_key, supabase_url, supabase_key

def test_connections(hf_token, groq_key, supabase_url, supabase_key):
    results = {}

    # Test Hugging Face
    if hf_token:
        try:
            from ai_engine import HuggingFaceEngine
            hf = HuggingFaceEngine(api_token=hf_token)
            hf.generate("اختبار", max_tokens=5)
            results["Hugging Face"] = {"status": "متصل", "color": "#10b981"}
        except Exception as e:
            results["Hugging Face"] = {"status": "خطأ", "color": "#ef4444", "error": str(e)}
    else:
        results["Hugging Face"] = {"status": "مفقود", "color": "#f59e0b"}

    # Test Groq
    if groq_key:
        try:
            from ai_engine import GroqEngine
            groq = GroqEngine(api_key=groq_key)
            groq.generate("اختبار", max_tokens=5)
            results["Groq"] = {"status": "متصل", "color": "#10b981"}
        except Exception as e:
            results["Groq"] = {"status": "خطأ", "color": "#ef4444", "error": str(e)}
    else:
        results["Groq"] = {"status": "مفقود", "color": "#f59e0b"}

    # Test Supabase
    if supabase_url and supabase_key:
        try:
            from storage import SupabaseStorage
            supabase = SupabaseStorage(url=supabase_url, key=supabase_key)
            supabase.list_files()
            results["Supabase"] = {"status": "متصل", "color": "#10b981"}
        except Exception as e:
            results["Supabase"] = {"status": "خطأ", "color": "#ef4444", "error": str(e)}
    else:
        results["Supabase"] = {"status": "مفقود", "color": "#f59e0b"}

    st.session_state.api_status = results

def display_connection_status():
    if "api_status" in st.session_state:
        st.sidebar.markdown("### 📡 حالة الاتصال")
        for service, result in st.session_state.api_status.items():
            st.sidebar.markdown(
                f'<p style="color: {result["color"]}; margin: 0.5rem 0; font-weight: 600;">• {service}: {result["status"]}</p>',
                unsafe_allow_html=True
            )
            if result.get("error"):
                with st.sidebar.expander(f"تفاصيل خطأ {service}"):
                    st.error(result["error"])

# ======================
# PERSONA SYSTEM (بدون أيموجي + بدون label_visibility)
# ======================
PERSONA_INFO = {
    "worker": {"name": "عامل", "description": "للموظفين والعاملين"},
    "employer": {"name": "صاحب عمل", "description": "لأصحاب العمل"},
    "lawyer": {"name": "محامي", "description": " للمحامين"},
    "judge": {"name": "قاضي", "description": " للقضاة"}
}

def select_persona():
    st.markdown("<div class='header'><h1>⚖️ الفوهر</h1><p>نظام قانون العمل السعودي الذكي</p></div>", unsafe_allow_html=True)
    st.markdown("## 👤 اختر دورك")

    # Create persona buttons with pure HTML/CSS (no label_visibility)
    persona_html = "<div class='persona-container'>"
    for persona_id, info in PERSONA_INFO.items():
        persona_html += f"""
        <div class="persona-button" onclick="document.getElementById('hidden_{persona_id}').click()">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{info['name']}</div>
            <div style="font-size: 0.9rem; opacity: 0.8;">{info['description']}</div>
        </div>
        """
    persona_html += "</div>"
    st.markdown(persona_html, unsafe_allow_html=True)

    # Hidden buttons for functionality (بدون label_visibility)
    cols = st.columns(4)
    for idx, (persona_id, info) in enumerate(PERSONA_INFO.items()):
        with cols[idx]:
            if st.button(f"اختر {info['name']}", key=f"hidden_{persona_id}"):
                st.session_state.persona = persona_id

    # Display selected persona
    if "persona" in st.session_state:
        persona = st.session_state.persona
        info = PERSONA_INFO[persona]
        st.markdown(f"""
        <div style='background-color: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;
                    margin-top: 1rem; border: 1px solid #374151; text-align: center;'>
            <p style='margin: 0; font-weight: 600;'>دورك الحالي: <span style='color: #D4AF37'>{info['name']}</span></p>
        </div>
        """, unsafe_allow_html=True)
        return persona
    return None

# ======================
# MAIN APP
# ======================
def main():
    hf_token, groq_key, supabase_url, supabase_key = setup_sidebar()
    os.environ["HUGGINGFACE_TOKEN"] = hf_token
    os.environ["GROQ_API_KEY"] = groq_key
    os.environ["SUPABASE_URL"] = supabase_url
    os.environ["SUPABASE_KEY"] = supabase_key

    persona = select_persona()
    if not persona:
        st.warning("⚠️ يرجى اختيار دورك أولاً")
        st.stop()

    # Get tools for persona
    try:
        from legal_tools import get_tools_for_persona, PERSONA_PROMPTS
        tools_list = get_tools_for_persona(persona)
        system_prompt = PERSONA_PROMPTS.get(persona, "")
    except Exception as e:
        st.error(f"خطأ في تحميل الأدوات: {str(e)}")
        st.stop()

    # Display tools
    st.markdown("## 🛠️ الأدوات المتاحة")
    st.markdown('<div class="tools-grid">', unsafe_allow_html=True)

    for tool in tools_list:
        tool_html = f"""
        <div class="tool-card" onclick="document.getElementById('tool_{tool['func']}').click()">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{tool['icon']}</div>
            <div style="font-weight: 600; margin-bottom: 0.5rem;">{tool['name']}</div>
            <div style="font-size: 0.85rem; opacity: 0.8;">{tool['description']}</div>
        </div>
        """
        st.markdown(tool_html, unsafe_allow_html=True)
        if st.button(f"فتح {tool['name']}", key=f"tool_{tool['func']}"):
            st.session_state.selected_tool = tool["func"]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Features
    with st.expander("🔍 بحث قانوني", expanded=False):
        query = st.text_input("ادخل كلمات البحث:")
        if query:
            try:
                from legal_database import get_legal_database
                db = get_legal_database()
                results = db.search_articles(query, limit=10)
                if results:
                    for result in results:
                        with st.expander(f"المادة {result['id']}: {result['title']}"):
                            st.markdown(f"**الفئة:** {result['category']}")
                            st.markdown(f"**المحتوى:** {result['content']}")
                else:
                    st.info("لا يوجد نتائج")
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

    with st.expander("💰 حساب نهاية الخدمة", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1: years = st.number_input("سنوات العمل:", min_value=0.0, value=5.0, step=0.5)
        with col2: salary = st.number_input("آخر راتب (ريال):", min_value=0, value=10000, step=1000)
        with col3: reason = st.selectbox("سبب الانتهاء:", ["استقالة", "فصل تعسفي", "تقاعد"])

        if st.button("📊 احسب مستحقاتي"):
            try:
                from legal_tools import calculate_end_of_service
                result = calculate_end_of_service(years, salary, reason)
                if "error" not in result:
                    st.success(f"مستحقاتك: **{result['benefit_amount']:,} ريال** ({result['benefit_days']} يوم)")
                else:
                    st.error(result["error"])
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

    with st.expander("🤖 مساعد قانوني ذكي", expanded=True):
        if st.session_state.get("api_status", {}).get("Groq", {}).get("status") != "متصل":
            st.warning("⚠️ قم بتوصيل API أولاً (Groq أو Hugging Face)")
        else:
            query = st.text_area("اسأل عن أي مسألة قانونية:", height=150)
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