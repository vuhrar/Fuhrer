# styles.py
"""
نظام التصميم الموحد للتطبيق — النسخة الاحترافية v2.0
Dark Mode احترافي مع دعم RTL الكامل
"""

MAIN_CSS = """
<style>
:root {
    --bg-primary:    #0a0f1e;
    --bg-secondary:  #111827;
    --bg-card:       #d1d5db; /* رمادي فاتح للخانات */
    --bg-hover:      #e5e7eb;
    --accent-blue:   #4a9eff;
    --accent-gold:   #f59e0b;
    --accent-green:  #4ade80;
    --accent-red:    #f87171;
    --accent-purple: #a78bfa;
    --text-primary:  #f1f5f9;
    --text-secondary:#94a3b8;
    --text-muted:    #64748b;
    --border:        #2d3748;
    --border-hover:  #4a5568;
    --shadow:        0 4px 24px rgba(0,0,0,0.4);
    --radius:        12px;
    --radius-sm:     8px;
    --transition:    all 0.25s ease;
}

* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Zain',  sans-serif;
    direction: rtl;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1526 0%, #111827 100%) !important;
    border-left: 1px solid var(--border);
}

[data-testid="stHeader"] { background: transparent !important; }

.stButton > button {
    background: linear-gradient(135deg, var(--accent-blue), #2563eb) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: var(--transition) !important;
    box-shadow: 0 2px 8px rgba(74, 158, 255, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(74, 158, 255, 0.5) !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background-color: var(--bg-card) !important;
    color: #ffffff !important; /* خط أبيض */
    border: 1px solid #9ca3af !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.2) !important;
}

.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-right: 4px solid var(--accent-blue);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin: 12px 0;
    box-shadow: var(--shadow);
    line-height: 1.8;
}

.card h2, .card h3 { color: var(--accent-blue); margin-bottom: 8px; }
.card p { color: var(--text-secondary); margin: 4px 0; }

.stat-card {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-hover));
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    text-align: center;
    box-shadow: var(--shadow);
    transition: var(--transition);
}

.stat-card:hover { transform: translateY(-4px); }
.stat-card .stat-value { font-size: 2rem; font-weight: 700; color: var(--accent-blue); }
.stat-card .stat-label { font-size: 0.85rem; color: var(--text-secondary); margin-top: 6px; }

.alert { border-radius: var(--radius-sm); padding: 14px 18px; margin: 8px 0; border-right: 4px solid; }
.alert.danger  { background: rgba(248,113,113,0.1); border-color: var(--accent-red);    color: #fca5a5; }
.alert.warn    { background: rgba(245,158,11,0.1);  border-color: var(--accent-gold);   color: #fcd34d; }
.alert.info    { background: rgba(74,158,255,0.1);  border-color: var(--accent-blue);   color: #93c5fd; }
.alert.success { background: rgba(74,222,128,0.1);  border-color: var(--accent-green);  color: #86efac; }

.section-title {
    font-size: 1.5rem; font-weight: 700; color: var(--text-primary);
    padding: 16px 0 8px; border-bottom: 2px solid var(--accent-blue); margin-bottom: 20px;
}

.info-box {
    background: rgba(74,158,255,0.08); border: 1px solid rgba(74,158,255,0.25);
    border-radius: var(--radius-sm); padding: 12px 16px; color: #93c5fd;
    font-size: 0.9rem; margin-bottom: 16px;
}

.badge { display: inline-block; padding: 3px 10px; border-radius: 50px; font-size: 0.75rem; font-weight: 600; }
.badge-blue   { background: rgba(74,158,255,0.15); color: var(--accent-blue); }
.badge-green  { background: rgba(74,222,128,0.15); color: var(--accent-green); }
.badge-red    { background: rgba(248,113,113,0.15); color: var(--accent-red); }
.badge-gold   { background: rgba(245,158,11,0.15);  color: var(--accent-gold); }

.logo-container { text-align: center; padding: 20px 0 10px; }
.logo-title {
    font-size: 4rem; font-weight: 800; /* تكبير الشعار للضعف */
    background: linear-gradient(135deg, #ffffff, var(--accent-blue));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    text-shadow: 0 10px 30px rgba(0,0,0,0.3);
    letter-spacing: -2px;
}
.logo-subtitle { font-size: 0.8rem; color: var(--text-muted); letter-spacing: 2px; }

.chat-bubble {
    max-width: 75%; padding: 12px 16px; border-radius: 16px; line-height: 1.7; font-size: 0.9rem;
}
.chat-bubble.user      { background: linear-gradient(135deg, var(--accent-blue), #2563eb); color: #fff; }
.chat-bubble.assistant { background: var(--bg-card); border: 1px solid var(--border); color: var(--text-primary); }

.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important; /* شريط أبيض */
    border-radius: var(--radius-sm) !important; gap: 4px; padding: 4px;
    border: 1px solid #e5e7eb !important;
}
.stTabs [data-baseweb="tab"] {
    color: #4b5563 !important; /* خط رمادي غامق للشريط الأبيض */
}
.stTabs [data-baseweb="tab"]  { background: transparent !important; color: var(--text-secondary) !important; border-radius: var(--radius-sm) !important; }
.stTabs [aria-selected="true"] { background: var(--accent-blue) !important; color: #fff !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-hover); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.fade-in { animation: fadeIn 0.4s ease forwards; }

@media (max-width: 768px) {
    .stat-card .stat-value { font-size: 1.5rem; }
    .section-title { font-size: 1.2rem; }
}
</style>
"""


def get_custom_styles() -> str:
    """إعادة CSS للتوافق مع الكود القديم."""
    return MAIN_CSS


def inject_styles():
    """حقن أنماط CSS في التطبيق."""
    import streamlit as st
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
