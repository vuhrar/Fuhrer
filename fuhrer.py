# -*- coding: utf-8 -*-
"""
Fuhrer - Saudi Labor Law Assistant | تصميم احترافي 8K
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ======================
# PROFESSIONAL 8K STYLES
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
        div[data-testid="stSidebar"] .stTextInput > div > div > input,
        div[data-testid="stSidebar"] .stButton > button {
            background-color: #1F2937 !important;
            color: #FFFFFF !important;
            border: 1px solid #D4AF37 !important;
        }

        /* ===== BUTTONS ===== */
        .stButton > button {
            background-color: #374151 !important;
            color: #FFFFFF !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 8px !important;
            padding: 0.75rem 2rem !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background-color: #D4AF37 !important;
            color: #111827 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* ===== INPUT FIELDS ===== */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #F9FAFB !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            color: #111827 !important;
            font-family: 'Cairo', sans-serif !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #D4AF37 !important;
            box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1) !important;
            outline: none !important;
        }

        /* ===== FILE UPLOADER ===== */
        .stFileUploader > div {
            background-color: #F9FAFB !important;
            border: 2px dashed #D4AF37 !important;
            border-radius: 12px !important;
            padding: 2rem !important;
            color: #111827 !important;
        }

        /* ===== EXPANDERS & CARDS ===== */
        .stExpander, [data-testid="stExpander"] {
            background-color: #1F2937 !important;
            border: 1px solid #374151 !important;
            border-radius: 12px !important;
            margin: 1rem 0 !important;
        }
        .stExpander > div:first-child {
            background-color: #374151 !important;
            color: #FFFFFF !important;
            border-radius: 12px 12px 0 0 !important;
        }

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px !important;
            background-color: #1F2937 !important;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #374151 !important;
            color: #FFFFFF !important;
            border-radius: 8px 8px 0 0 !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            border: 1px solid #374151 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #D4AF37 !important;
            color: #111827 !important;
            border-bottom: 1px solid #111827 !important;
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
            font-family: 'Cairo', sans-serif !important;
            font-weight: 600 !important;
        }
        .persona-button:hover {
            background-color: #D4AF37 !important;
            color: #111827 !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 8px 16px rgba(212, 175, 55, 0.3) !important;
            border-color: #D4AF37 !important;
        }
        .persona-button.selected {
            background-color: #D4AF37 !important;
            color: #111827 !important;
            border-color: #D4AF37 !important;
        }

        /* ===== HEADER ===== */
        .header {
            background: linear-gradient(135deg, #1F2937 0%, #374151 100%) !important;
            color: #FFFFFF !important;
            padding: 2rem 1rem !important;
            border-radius: 0 0 15px 15px !important;
            margin-bottom: 2rem !important;
            border: 1px solid #D4AF37 !important;
            box-shadow: 0 4px 6px rgba(212, 175, 55, 0.1) !important;
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
        .stAlert-error {
            background-color: rgba(239, 68, 68, 0.2) !important;
            border-color: #ef4444 !important;
        }
        .stAlert-warning {
            background-color: rgba(245, 158, 11, 0.2) !important;
            border-color: #f59e0b !important;
        }
        .stAlert-success {
            background-color: rgba(16, 185, 129, 0.2) !important;
            border-color: #10b981 !important;
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
        ::-webkit-scrollbar-thumb:hover {
            background: #D4AF37;
        }

        /* ===== TOOL BUTTONS GRID ===== */
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
        }
        .tool-card:hover {
            border-color: #D4AF37 !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 8px 16px rgba(212, 175, 55, 0.2) !important;
        }
    </style>
    """
    + """
    <script>
        // Add dynamic interaction for persona buttons
        document.addEventListener('DOMContentLoaded', function() {
            const personaButtons = document.querySelectorAll('.persona-button');
            personaButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Remove selected class from all buttons
                    personaButtons.forEach(btn => btn.classList.remove('selected'));
                    // Add selected class to clicked button
                    this.classList.add('selected');
                });
            });
        });
    </script>
    """

# Inject styles
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
    """Configure sidebar with professional dark theme"""
    st.sidebar.markdown("## ⚙️ إعدادات API")
    st.sidebar.markdown("---")

    # API Keys Input with professional styling
    api_config = {
        "HUGGINGFACE_TOKEN": st.sidebar.text_input(
            "Hugging Face Token",
            type="password",
            value=os.getenv("HUGGINGFACE_TOKEN", ""),
            key="hf_token",
            label_visibility="collapsed"
        ),
        "GROQ_API_KEY": st.sidebar.text_input(
            "Groq API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            key="groq_token",
            label_visibility="collapsed"
        ),
        "SUPABASE_URL": st.sidebar.text_input(
            "Supabase URL",
            value=os.getenv("SUPABASE_URL", ""),
            key="supabase_url",
            label_visibility="collapsed"
        ),
        "SUPABASE_KEY": st.sidebar.text_input(
            "Supabase Key",
            type="password",
            value=os.getenv("SUPABASE_KEY", ""),
            key="supabase_key",
            label_visibility="collapsed"
        )
    }

    # Add labels with HTML for better styling
    st.sidebar.markdown("""
    <div style='color: #D4AF37; margin-top: 1rem;'>
        <p style='margin: 0.5rem 0; font-size: 0.9rem;'><b>🤗 Hugging Face Token</b></p>
        <p style='margin: 0.5rem 0; font-size: 0.9rem;'><b>⚡ Groq API Key</b></p>
        <p style='margin: 0.5rem 0; font-size: 0.9rem;'><b>🗄️ Supabase URL</b></p>
        <p style='margin: 0.5rem 0; font-size: 0.9rem;'><b>🔑 Supabase Key</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Test Connection Button
    if st.sidebar.button("🔍 اختبار الاتصال", use_container_width=True, key="test_connection"):
        with st.spinner("جاري الاختبار..."):
            test_connections(api_config)

    # Display connection status
    display_connection_status()

    return api_config

def test_connections(api_config):
    """Test all API connections"""
    results = {}

    # Test Hugging Face
    if api_config["HUGGINGFACE_TOKEN"]:
        try:
            from ai_engine import HuggingFaceEngine
            hf = HuggingFaceEngine(api_token=api_config["HUGGINGFACE_TOKEN"])
            hf.generate("اختبار", max_tokens=5)
            results["Hugging Face"] = {"status": "متصل", "color": "#10b981"}
        except Exception as e:
            results["Hugging Face"] = {"status": "خطأ", "color": "#ef4444", "error": str(e)}
    else:
        results["Hugging Face"] = {"status": "مفقود", "color": "#f59e0b"}

    # Test Groq
    if api_config["GROQ_API_KEY"]:
        try:
            from ai_engine import GroqEngine
            groq = GroqEngine(api_key=api_config["GROQ_API_KEY"])
            groq.generate("اختبار", max_tokens=5)
            results["Groq"] = {"status": "متصل", "color": "#10b981"}
        except Exception as e:
            results["Groq"] = {"status": "خطأ", "color": "#ef4444", "error": str(e)}
    else:
        results["Groq"] = {"status": "مفقود", "color": "#f59e0b"}

    # Test Supabase
    if api_config["SUPABASE_URL"] and api_config["SUPABASE_KEY"]:
        try:
            from storage import SupabaseStorage
            supabase = SupabaseStorage(url=api_config["SUPABASE_URL"], key=api_config["SUPABASE_KEY"])
            supabase.list_files()
            results["Supabase"] = {"status": "متصل", "color": "#10b981"}
        except Exception as e:
            results["Supabase"] = {"status": "خطأ", "color": "#ef4444", "error": str(e)}
    else:
        results["Supabase"] = {"status": "مفقود", "color": "#f59e0b"}

    st.session_state.api_status = results

def display_connection_status():
    """Display API connection status with professional colors"""
    if "api_status" in st.session_state:
        st.sidebar.markdown("### 📡 حالة الاتصال")
        for service, result in st.session_state.api_status.items():
            color = result["color"]
            status = result["status"]
            st.sidebar.markdown(
                f'<p style="color: {color}; margin: 0.5rem 0; font-weight: 600;">• {service}: {status}</p>',
                unsafe_allow_html=True
            )
            if result.get("error") and st.sidebar.button(f"تفاصيل {service}", key=f"err_{service}"):
                st.sidebar.error(result["error"])

# ======================
# PERSONA SYSTEM (بدون أيموجي)
# ======================
PERSONA_INFO = {
    "worker": {"name": "عامل", "description": "للموظفين والعاملين", "color": "#10b981"},
    "employer": {"name": "صاحب عمل", "description": "لأصحاب العمل", "color": "#3b82f6"},
    "lawyer": {"name": "محامي", "description": " للمحامين", "color": "#ef4444"},
    "judge": {"name": "قاضي", "description": " للقضاة", "color": "#8b5cf6"}
}

def select_persona():
    """Personas selection with professional design"""
    st.markdown("<div class='header'><h1>⚖️ Fuhrer</h1><p>نظام قانون العمل السعودي الذكي</p></div>", unsafe_allow_html=True)
    st.markdown("## 👤 اختر دورك")

    # Create persona buttons with HTML/CSS
    persona_html = """
    <div class="persona-container">
    """
    for persona_id, info in PERSONA_INFO.items():
        persona_html += f"""
        <div class="persona-button" onclick="document.getElementById('{persona_id}_btn').click()">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{info['name']}</div>
            <div style="font-size: 0.9rem; opacity: 0.8;">{info['description']}</div>
        </div>
        """
    persona_html += """
    </div>
    """

    st.markdown(persona_html, unsafe_allow_html=True)

    # Hidden buttons for functionality
    cols = st.columns(4)
    for idx, (persona_id, info) in enumerate(PERSONA_INFO.items()):
        with cols[idx]:
            if st.button("", key=f"{persona_id}_btn", label_visibility="collapsed"):
                st.session_state.persona = persona_id

    # Display selected persona
    if "persona" in st.session_state:
        persona = st.session_state.persona
        info = PERSONA_INFO[persona]
        st.markdown(f"""
        <div style='background-color: {info['color']}22; padding: 1rem; border-radius: 8px; margin-top: 1rem; border: 1px solid {info['color']}'>
            <p style='margin: 0; font-weight: 600;'>دورك الحالي: <span style='color: {info['color']}'>{info['name']}</span></p>
        </div>
        """, unsafe_allow_html=True)
        return persona

    return None

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

    # ======================
    # TOOLS GRID
    # ======================
    try:
        from legal_tools import get_tools_for_persona, PERSONA_PROMPTS
        tools_list = get_tools_for_persona(persona)
        system_prompt = PERSONA_PROMPTS.get(persona, "")
    except Exception as e:
        st.error(f"خطأ في تحميل الأدوات: {str(e)}")
        st.stop()

    st.markdown("## 🛠️ الأدوات المتاحة")
    st.markdown('<div class="tools-grid">', unsafe_allow_html=True)

    for tool in tools_list:
        tool_html = f"""
        <div class="tool-card" onclick="document.getElementById('{tool['func']}_btn').click()">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{tool['icon']}</div>
            <div style="font-weight: 600; margin-bottom: 0.5rem;">{tool['name']}</div>
            <div style="font-size: 0.85rem; opacity: 0.8;">{tool['description']}</div>
        </div>
        """
        st.markdown(tool_html, unsafe_allow_html=True)
        if st.button("", key=f"{tool['func']}_btn", label_visibility="collapsed"):
            st.session_state.selected_tool = tool["func"]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ======================
    # FEATURES
    # ======================
    st.markdown("---")

    # 1. Legal Search
    with st.expander("🔍 بحث قانوني", expanded=False):
        query = st.text_input("ادخل كلمات البحث:", key="search_query")
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

    # 2. Document Analysis
    with st.expander("📄 تحليل مستندات", expanded=False):
        uploaded = st.file_uploader("رفع ملف (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"], key="doc_upload")
        if uploaded:
            try:
                from file_processing import process_uploaded_file
                text = process_uploaded_file(uploaded)
                st.success("✅ تم استخراج النص بنجاح!")
                st.text_area("النص المستخرج:", text[:2000], height=200, key="extracted_text")
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

    # 3. End of Service Calculation
    with st.expander("💰 حساب نهاية الخدمة", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1: years = st.number_input("سنوات العمل:", min_value=0.0, value=5.0, step=0.5, key="yos_years")
        with col2: salary = st.number_input("آخر راتب (ريال):", min_value=0, value=10000, step=1000, key="yos_salary")
        with col3: reason = st.selectbox("سبب الانتهاء:", ["استقالة", "فصل تعسفي", "تقاعد"], key="yos_reason")

        if st.button("📊 احسب مستحقاتي", key="calculate_eos"):
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
        if st.session_state.get("api_status", {}).get("Groq", {}).get("status") != "متصل":
            st.warning("⚠️ قم بتوصيل API أولاً (Groq أو Hugging Face)")
        else:
            query = st.text_area("اسأل عن أي مسألة قانونية:", key="ai_query", height=150)
            if query and st.button("💬 ارسال", key="send_query"):
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