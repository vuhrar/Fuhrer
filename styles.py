# styles.py
MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Zain:wght@400;500;700;900&display=swap');
font-family: 'Zain', sans-serif !important;

*, *::before, *::after { box-sizing: border-box !important; font-family: 'Zain', sans-serif !important; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"] {
    background-color: #1c1c1e !important; color: #ffffff !important; direction: rtl !important;
}
[data-testid="stSidebar"], #MainMenu, footer, header { display: none !important; }
.main .block-container { max-width: 900px !important; padding: 0 16px 80px !important; margin: 0 auto !important; }

.app-title {
    text-align: center; padding: 40px 0 10px; font-size: 6.4rem; font-weight: 700;
    background: linear-gradient(135deg, #ffffff, #4a9eff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; text-shadow: 0 10px 30px rgba(0,0,0,0.4);
    letter-spacing: -0.02em; margin-bottom: 10px;
}

.persona-card {
    background: #2c2c2e; border: 2px solid #c9a84c; border-radius: 20px;
    padding: 40px 20px; text-align: center; transition: all 0.3s ease;
}
.persona-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(201,168,76,0.2); border-color: #f0c040; }
.pc-icon { font-size: 3rem; margin-bottom: 15px; }
.pc-title { font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-bottom: 10px; }
.pc-sub { font-size: 0.9rem; color: #aaaaaa; line-height: 1.6; }

.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important; border-radius: 8px !important; gap: 4px; padding: 4px;
    border: 1px solid #e5e7eb !important;
}
.stTabs [data-baseweb="tab"] { color: #4b5563 !important; border-radius: 8px !important; }
.stTabs [aria-selected="true"] { background: #4a9eff !important; color: #fff !important; }

.stButton > button {
    background: linear-gradient(135deg, #4a9eff, #2563eb) !important;
    color: #fff !important; border: none !important; border-radius: 12px !important;
    padding: 10px 20px !important; font-weight: 700 !important; font-size: 14px !important;
    transition: all 0.25s ease !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; }

.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #2c2c2e !important; color: #ffffff !important;
    border: 1px solid #3a3a3c !important; border-radius: 8px !important;
    padding: 12px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
    border-color: #4a9eff !important; box-shadow: 0 0 0 2px rgba(74,158,255,0.2) !important;
}

.bubble-user {
    background: #2c3e50; border-radius: 20px 20px 5px 20px; padding: 15px 20px;
    margin: 10px 0 10px 15%; color: #fff; font-size: 1rem; line-height: 1.7;
}
.bubble-ai {
    background: #2c2c2e; border-right: 4px solid #c9a84c; border-radius: 20px 20px 20px 5px;
    padding: 15px 20px; margin: 10px 15% 10px 0; color: #fff; font-size: 1rem; line-height: 1.8;
}

.section-title {
    font-size: 1.2rem; font-weight: 800; color: #c9a84c; margin: 25px 0 15px;
    display: flex; align-items: center; gap: 10px;
}
.section-title::after { content: ""; flex: 1; height: 1px; background: #3a3a3c; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #1c1c1e; }
::-webkit-scrollbar-thumb { background: #3a3a3c; border-radius: 3px; }
</style>
"""
