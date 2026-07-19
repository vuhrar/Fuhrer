# styles.py
"""نظام التصميم الموحد — Dark Mode + RTL"""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');

:root {
    --bg-primary:    #0a0f1e;
    --bg-secondary:  #111827;
    --bg-card:       #2c2c2e;
    --bg-hover:      #3a3a3c;
    --accent-blue:   #4a9eff;
    --accent-gold:   #c9a84c;
    --accent-green:  #4ade80;
    --accent-red:    #f87171;
    --text-primary:  #ffffff;
    --text-secondary:#aaaaaa;
    --text-muted:    #64748b;
    --border:        #3a3a3c;
}

*, *::before, *::after { box-sizing: border-box !important; font-family: 'Tajawal', sans-serif !important; }

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    direction: rtl !important;
}

[data-testid="stSidebar"], #MainMenu, footer, header { display: none !important; }
.main .block-container { max-width: 900px !important; padding: 0 16px 80px !important; margin: 0 auto !important; }

/* ========== العنوان الرئيسي ========== */
.app-title {
    text-align: center; padding: 40px 0 10px; font-size: 6.4rem; font-weight: 900;
    background: linear-gradient(135deg, #ffffff, var(--accent-blue));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; text-shadow: 0 10px 30px rgba(0,0,0,0.4);
    letter-spacing: -0.02em; margin-bottom: 10px;
}

/* ========== بطاقات اختيار الشخصية ========== */
.persona-card {
    background: #2c2c2e; border: 2px solid var(--accent-gold); border-radius: 20px;
    padding: 40px 20px; text-align: center; cursor: pointer; transition: all 0.3s ease;
}
.persona-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(201,168,76,0.2); border-color: #f0c040; }
.pc-icon { font-size: 3rem; margin-bottom: 15px; }
.pc-title { font-size: 1.5rem; font-weight: 800; color: var(--text-primary); margin-bottom: 10px; }
.pc-sub { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.6; }

/* ========== شريط التنقل ========== */
.nav-bar { display: flex; justify-content: center; gap: 15px; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
.nav-item { cursor: pointer; padding: 8px 20px; border-radius: 20px; font-weight: 600; font-size: 0.95rem; transition: 0.2s; }
.nav-item.active { background: var(--accent-gold); color: #1c1c1e; }

/* ========== تبويبات ========== */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important; border-radius: 8px !important; gap: 4px; padding: 4px;
    border: 1px solid #e5e7eb !important;
}
.stTabs [data-baseweb="tab"] { color: #4b5563 !important; border-radius: 8px !important; }
.stTabs [aria-selected="true"] { background: var(--accent-blue) !important; color: #fff !important; }

/* ========== أزرار ========== */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-blue), #2563eb) !important;
    color: #fff !important; border: none !important; border-radius: 12px !important;
    padding: 10px 20px !important; font-weight: 700 !important; font-size: 14px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 8px rgba(74,158,255,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(74,158,255,0.5) !important;
}

/* ========== حقول الإدخال ========== */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #d1d5db !important; color: #1f2937 !important;
    border: 1px solid #9ca3af !important; border-radius: 8px !important;
    padding: 12px !important; font-weight: 500 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(74,158,255,0.2) !important;
}

/* ========== فقاعات المحادثة ========== */
.bubble-user {
    background: #2c3e50; border-radius: 20px 20px 5px 20px; padding: 15px 20px;
    margin: 10px 0 10px 15%; color: #fff; font-size: 1rem; line-height: 1.7;
}
.bubble-ai {
    background: #2c2c2e; border-right: 4px solid var(--accent-gold); border-radius: 20px 20px 20px 5px;
    padding: 15px 20px; margin: 10px 15% 10px 0; color: #fff; font-size: 1rem; line-height: 1.8;
}

/* ========== بطاقات عامة ========== */
.card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-right: 4px solid var(--accent-blue); border-radius: 12px;
    padding: 20px 24px; margin: 12px 0; line-height: 1.8;
}

/* ========== تنبيهات ========== */
.alert { border-radius: 8px; padding: 14px 18px; margin: 8px 0; border-right: 4px solid; }
.alert.danger  { background: rgba(248,113,113,0.1); border-color: var(--accent-red);    color: #fca5a5; }
.alert.warn    { background: rgba(245,158,11,0.1);  border-color: var(--accent-gold);   color: #fcd34d; }
.alert.info    { background: rgba(74,158,255,0.1);  border-color: var(--accent-blue);   color: #93c5fd; }
.alert.success { background: rgba(74,222,128,0.1);  border-color: var(--accent-green);  color: #86efac; }

/* ========== شارات ========== */
.badge { display: inline-block; padding: 3px 10px; border-radius: 50px; font-size: 0.75rem; font-weight: 600; }
.badge-blue   { background: rgba(74,158,255,0.15); color: var(--accent-blue); }
.badge-green  { background: rgba(74,222,128,0.15); color: var(--accent-green); }
.badge-red    { background: rgba(248,113,113,0.15); color: var(--accent-red); }
.badge-gold   { background: rgba(245,158,11,0.15);  color: var(--accent-gold); }

/* ========== عناوين الأقسام ========== */
.section-title {
    font-size: 1.2rem; font-weight: 800; color: var(--accent-gold); margin: 25px 0 15px;
    display: flex; align-items: center; gap: 10px;
}
.section-title::after { content: ""; flex: 1; height: 1px; background: var(--border); }

/* ========== شريط تمرير ========== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ========== حركات ========== */
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.fade-in { animation: fadeIn 0.4s ease forwards; }
</style>
"""

def get_custom_styles():
    return MAIN_CSS
