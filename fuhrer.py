import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
import ai_engine, analysis_engine, legal_tools, file_processing, storage

st.set_page_config(
    page_title="Führer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── إخفاء الشريط الجانبي نهائياً ──────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CSS الكامل
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');

*, *::before, *::after {
    box-sizing: border-box !important;
    font-family: 'Tajawal', sans-serif !important;
}

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"],
.main {
    background-color: #1c1f24 !important;
    color: #f0f0f0 !important;
    direction: rtl !important;
}

#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stHeader"] { height: 0 !important; }

.main .block-container {
    max-width: 900px !important;
    padding: 1rem 1.2rem 3rem !important;
    margin: 0 auto !important;
}

/* ── الشريط العلوي ── */
.top-header {
    background: #23272e;
    border-bottom: 2px solid #c9a84c;
    border-radius: 16px 16px 0 0;
    padding: 18px 24px 14px;
    text-align: center;
    margin-bottom: 0;
}
.top-header h1 {
    font-size: 2rem !important;
    font-weight: 900 !important;
    color: #c9a84c !important;
    margin: 0 !important;
    letter-spacing: 0.04em;
}
.top-header .sub {
    font-size: 0.8rem;
    color: #888;
    margin-top: 2px;
}

/* ── شريط التنقل الأفقي ── */
.nav-bar {
    background: #23272e;
    border-bottom: 1px solid #2e3340;
    padding: 10px 16px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
    margin-bottom: 16px;
    border-radius: 0 0 16px 16px;
}
.nav-bar .stButton > button {
    background: #2a2f38 !important;
    color: #ccc !important;
    border: 1px solid #3a3f4a !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    min-height: 40px !important;
    transition: all 0.15s !important;
}
.nav-bar .stButton > button:hover {
    background: #2e3440 !important;
    border-color: #c9a84c !important;
    color: #c9a84c !important;
}

/* ── أزرار الشخصية ── */
.persona-bar {
    display: flex;
    gap: 10px;
    margin: 12px 0;
}

/* ── أزرار عامة ── */
.stButton > button {
    background: #23272e !important;
    color: #f0f0f0 !important;
    border: 1px solid #3a3f4a !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    min-height: 44px !important;
    width: 100% !important;
    transition: all 0.15s !important;
    white-space: normal !important;
    word-break: keep-all !important;
}
.stButton > button:hover {
    border-color: #c9a84c !important;
    color: #c9a84c !important;
    background: #2a2f38 !important;
}

/* زر الإرسال مميز */
.send-btn .stButton > button {
    background: #c9a84c !important;
    color: #1c1f24 !important;
    border: none !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
}
.send-btn .stButton > button:hover {
    background: #d4b55a !important;
    color: #1c1f24 !important;
}

/* ── بطاقات ── */
.card {
    background: #23272e;
    border: 1px solid #2e3340;
    border-right: 3px solid #c9a84c;
    border-radius: 14px;
    padding: 16px 20px;
    margin: 10px 0;
    color: #f0f0f0 !important;
    line-height: 1.8;
}
.card.blue   { border-right-color: #4a9eff; }
.card.green  { border-right-color: #4ade80; }
.card.red    { border-right-color: #ff5a5a; }

/* ── تنبيهات ── */
.alert {
    border-radius: 10px;
    padding: 10px 16px;
    margin: 6px 0;
    font-size: 0.88rem;
    line-height: 1.65;
}
.alert.warn   { background:#2a2516; border-right:3px solid #c9a84c; color:#e8c96a !important; }
.alert.danger { background:#2a1616; border-right:3px solid #ff5a5a; color:#ff9090 !important; }
.alert.ok     { background:#162a1e; border-right:3px solid #4ade80; color:#86f0b0 !important; }
.alert.info   { background:#16222a; border-right:3px solid #4a9eff; color:#95cbff !important; }

/* ── إحصائيات ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px,1fr));
    gap: 10px;
    margin: 12px 0;
}
.stat-box {
    background: #23272e;
    border: 1px solid #2e3340;
    border-radius: 12px;
    padding: 14px;
    text-align: center;
}
.stat-box .v { font-size: 1.4rem; font-weight: 800; color: #c9a84c; }
.stat-box .l { font-size: 0.72rem; color: #888; margin-top: 4px; }

/* ── الدردشة ── */
.chat-wrap {
    background: #1e2228;
    border: 1px solid #2e3340;
    border-radius: 16px;
    padding: 14px;
    min-height: 200px;
    max-height: 55vh;
    overflow-y: auto;
    margin-bottom: 12px;
}
.chat-wrap::-webkit-scrollbar { width: 3px; }
.chat-wrap::-webkit-scrollbar-thumb { background: #3a3f4a; border-radius: 2px; }

.bubble-user {
    background: #1e2d45;
    border: 1px solid #2a4060;
    border-radius: 14px 14px 4px 14px;
    padding: 12px 16px;
    margin: 8px 0 8px 10%;
    color: #dce8ff !important;
    font-size: 0.92rem;
    line-height: 1.75;
}
.bubble-ai {
    background: #23272e;
    border: 1px solid #2e3340;
    border-right: 3px solid #c9a84c;
    border-radius: 14px 14px 14px 4px;
    padding: 12px 16px;
    margin: 8px 10% 8px 0;
    color: #f0f0f0 !important;
    font-size: 0.92rem;
    line-height: 1.8;
}
.bubble-ai.adv { border-right-color: #4a9eff; }
.bubble-meta { font-size: 0.68rem; color: #555; margin-top: 4px; }

/* ── حقول الإدخال ── */
.stTextArea textarea, .stTextInput input {
    background: #23272e !important;
    color: #f0f0f0 !important;
    border: 1.5px solid #3a3f4a !important;
    border-radius: 12px !important;
    direction: rtl !important;
    font-size: 0.92rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #c9a84c !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.12) !important;
}
.stSelectbox > div > div, .stNumberInput input {
    background: #23272e !important;
    color: #f0f0f0 !important;
    border: 1.5px solid #3a3f4a !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] {
    background: #23272e !important;
    border: 2px dashed #3a3f4a !important;
    border-radius: 14px !important;
}

/* ── خط فاصل ── */
hr { border-color: #2e3340 !important; margin: 14px 0 !important; }

/* ── expander ── */
.streamlit-expanderHeader {
    background: #23272e !important;
    color: #c9a84c !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}
.streamlit-expanderContent {
    background: #1e2228 !important;
    border: 1px solid #2e3340 !important;
}

/* ── progress ── */
.stProgress > div > div { background: #c9a84c !important; }

/* ── موبايل ── */
@media (max-width: 600px) {
    .main .block-container { padding: 0.5rem 0.6rem 2rem !important; }
    .top-header h1 { font-size: 1.5rem !important; }
    .bubble-user { margin-left: 2% !important; }
    .bubble-ai   { margin-right: 2% !important; }
    .stat-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .nav-bar .stButton > button {
        font-size: 0.78rem !important;
        padding: 6px 10px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# تهيئة الحالة
# ══════════════════════════════════════════════════════════════════════════════
_saved = storage.load_settings()
_defs  = {
    "persona":      "lawyer",
    "active_tool":  None,
    "active_nav":   None,
    "current_sid":  None,
    "current_msgs": [],
    "docs_text":    [],
    "preset_name":  _saved.get("preset_name", list(ai_engine.PRESETS.keys())[0]),
    "api_key":      _saved.get("api_key",""),
    "custom_url":   _saved.get("custom_url",""),
    "custom_model": _saved.get("custom_model",""),
    "custom_fmt":   _saved.get("custom_fmt","openai"),
    "pending":      "",
}
for k,v in _defs.items():
    if k not in st.session_state:
        st.session_state[k] = v

def ai_call(prompt, history, system):
    return ai_engine.call_ai(
        prompt, history, system,
        preset_name  = st.session_state.preset_name,
        api_key      = st.session_state.api_key,
        custom_url   = st.session_state.custom_url,
        custom_model = st.session_state.custom_model,
        custom_fmt   = st.session_state.custom_fmt,
    )

def nav(key):
    st.session_state.active_nav  = None if st.session_state.active_nav == key else key
    st.session_state.active_tool = None
    st.rerun()

def tool(key):
    st.session_state.active_tool = None if st.session_state.active_tool == key else key
    st.session_state.active_nav  = None
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# الرأس + شريط التنقل
# ══════════════════════════════════════════════════════════════════════════════
persona_color = "#c9a84c" if st.session_state.persona == "lawyer" else "#4a9eff"
persona_label = "⚖️ المحامي"   if st.session_state.persona == "lawyer" else "🧑 المستشار"

st.markdown(f"""
<div class='top-header'>
  <h1>Führer</h1>
  <div class='sub' style='color:{persona_color};font-weight:700;'>{persona_label}</div>
</div>
""", unsafe_allow_html=True)

# شريط التنقل الأفقي
with st.container():
    st.markdown("<div class='nav-bar'>", unsafe_allow_html=True)
    n1,n2,n3,n4,n5,n6,n7 = st.columns(7)
    with n1:
        if st.button("⊞ لوحة التحكم",   key="nav_dash"): nav("dashboard")
    with n2:
        if st.button("⚙️ الإعدادات",     key="nav_set"):  nav("settings")
    with n3:
        if st.button("🔌 الاتصال",       key="nav_conn"): nav("connection")
    with n4:
        if st.button("💬 الجلسات",       key="nav_sess"): nav("sessions")
    with n5:
        lbl = "⚖️ ✅" if st.session_state.persona=="lawyer" else "⚖️ محامي"
        if st.button(lbl, key="nav_law"):
            st.session_state.persona    = "lawyer"
            st.session_state.active_tool = None
            st.rerun()
    with n6:
        lbl = "🧑 ✅" if st.session_state.persona=="advisor" else "🧑 مستشار"
        if st.button(lbl, key="nav_adv"):
            st.session_state.persona    = "advisor"
            st.session_state.active_tool = None
            st.rerun()
    with n7:
        if st.button("🧭 تحليل ١٨", key="nav_deep"): tool("deep_analysis")
    st.markdown("</div>", unsafe_allow_html=True)

# ── أدوات الشخصية ──
tool_cols = st.columns(6)
for i, (icon, label, key) in enumerate(legal_tools.TOOLS[st.session_state.persona]):
    with tool_cols[i]:
        active = st.session_state.active_tool == key
        lbl    = f"{'▶ ' if active else ''}{icon}\n{label}"
        if st.button(lbl, key=f"t_{key}", use_container_width=True):
            tool(key)

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# لوحات التنقل
# ══════════════════════════════════════════════════════════════════════════════
active_nav = st.session_state.active_nav

if active_nav == "dashboard":
    st.markdown("## ⊞ لوحة التحكم")
    sessions = storage.list_sessions()
    st.markdown(f"""
    <div class='stat-grid'>
      <div class='stat-box'><div class='v'>{len(sessions)}</div><div class='l'>الجلسات</div></div>
      <div class='stat-box'><div class='v'>{len(st.session_state.docs_text)}</div><div class='l'>مستندات</div></div>
      <div class='stat-box'><div class='v'>{len(st.session_state.current_msgs)}</div><div class='l'>رسائل الجلسة</div></div>
      <div class='stat-box'><div class='v'>{"✅" if st.session_state.api_key else "❌"}</div><div class='l'>الاتصال</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_nav == "settings":
    st.markdown("## ⚙️ الإعدادات")
    if st.button("🗑 مسح كل الجلسات", use_container_width=False):
        for s in storage.list_sessions():
            storage.delete_session(s["id"])
        st.session_state.current_sid  = None
        st.session_state.current_msgs = []
        st.success("تم مسح جميع الجلسات.")
        st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_nav == "connection":
    st.markdown("## 🔌 الاتصال بالخادم")
    new_preset = st.selectbox("النموذج", list(ai_engine.PRESETS.keys()),
        index = list(ai_engine.PRESETS.keys()).index(st.session_state.preset_name)
                if st.session_state.preset_name in ai_engine.PRESETS else 0)
    st.session_state.preset_name = new_preset

    if new_preset == "⚙️ مخصص":
        st.session_state.custom_url   = st.text_input("رابط API",    value=st.session_state.custom_url)
        st.session_state.custom_model = st.text_input("اسم النموذج", value=st.session_state.custom_model)
        st.session_state.custom_fmt   = st.selectbox("الصيغة", ["openai","gemini","anthropic"])

    st.session_state.api_key = st.text_input(
        "مفتاح API", value=st.session_state.api_key,
        type="password", placeholder="AIza... أو sk-..."
    )
    key_ok = bool(st.session_state.api_key.strip())
    c = "#4ade80" if key_ok else "#ff5a5a"
    t = "✅ متصل" if key_ok else "❌ غير متصل — أدخل مفتاح API"
    st.markdown(f"<div class='alert {'ok' if key_ok else 'danger'}'>{t}</div>", unsafe_allow_html=True)

    if st.button("💾 حفظ", use_container_width=False):
        storage.save_settings({"preset_name":st.session_state.preset_name,
                                "custom_url":st.session_state.custom_url,
                                "custom_model":st.session_state.custom_model,
                                "custom_fmt":st.session_state.custom_fmt})
        st.success("تم الحفظ.")
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_nav == "sessions":
    st.markdown("## 💬 الجلسات")
    if st.button("➕ جلسة جديدة", use_container_width=False):
        sid = storage.new_session_id()
        st.session_state.current_sid  = sid
        st.session_state.current_msgs = []
        storage.save_session(sid, {"name":"جلسة جديدة","messages":[],"persona":st.session_state.persona})
        st.session_state.active_nav   = None
        st.rerun()

    for s in storage.list_sessions()[:8]:
        icon = "⚖️" if s.get("persona")=="lawyer" else "🧑"
        cur  = "🟢 " if s["id"] == st.session_state.current_sid else ""
        cc1, cc2 = st.columns([6,1])
        with cc1:
            if st.button(f"{cur}{icon} {s['name'][:18]} ({s['count']})", key=f"s_{s['id']}", use_container_width=True):
                d = storage.load_session(s["id"])
                st.session_state.current_sid  = s["id"]
                st.session_state.current_msgs = d.get("messages",[])
                st.session_state.persona      = d.get("persona","lawyer")
                st.session_state.active_nav   = None
                st.rerun()
        with cc2:
            if st.button("🗑", key=f"d_{s['id']}"):
                storage.delete_session(s["id"])
                if st.session_state.current_sid == s["id"]:
                    st.session_state.current_sid  = None
                    st.session_state.current_msgs = []
                st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# لوحة الأداة النشطة
# ══════════════════════════════════════════════════════════════════════════════
active_tool = st.session_state.active_tool

if active_tool == "calculator":
    st.markdown("## 🧮 حاسبة المستحقات")
    c1,c2,c3 = st.columns(3)
    with c1: basic   = st.number_input("الأساسي (ريال)", min_value=0.0, step=500.0)
    with c2: total   = st.number_input("الإجمالي (ريال)",min_value=0.0, step=500.0)
    with c3: years   = st.number_input("سنوات الخدمة",  min_value=0.0, step=0.5)
    c4,c5 = st.columns(2)
    with c4: arbitrary = st.checkbox("فصل تعسفي (م.77)")
    with c5: delay_m   = st.number_input("أشهر تأخير الراتب", min_value=0, step=1)
    if st.button("⚡ احسب المستحقات", use_container_width=False) and basic>0 and years>0:
        res = legal_tools.calculate_eosb(basic, total if total>0 else basic, years, arbitrary, delay_m)
        st.markdown(f"""
        <div class='stat-grid'>
          <div class='stat-box'><div class='v'>{res['eosb']:,.0f}</div><div class='l'>مكافأة نهاية الخدمة</div></div>
          <div class='stat-box'><div class='v'>{res['arbitrary']:,.0f}</div><div class='l'>تعويض تعسفي</div></div>
          <div class='stat-box'><div class='v'>{res['delay']:,.0f}</div><div class='l'>تعويض تأخير</div></div>
          <div class='stat-box' style='border:2px solid #c9a84c;'>
            <div class='v' style='font-size:1.6rem;'>{res['grand']:,.0f}</div>
            <div class='l'>الإجمالي (ريال)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        for d in res["details"]:
            if d: st.markdown(f"<div class='alert info'>📌 {d}</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_tool == "email_scan":
    st.markdown("## 📧 فحص المراسلات")
    uploaded = st.file_uploader("ارفع ملفات المراسلات", type=["pdf","txt","docx"], accept_multiple_files=True)
    manual   = st.text_area("أو الصق النص مباشرة", height=130)
    if st.button("🔍 فحص الآن", use_container_width=False):
        combined = manual
        if uploaded:
            for f in uploaded:
                combined += "\n\n" + file_processing.extract_text_from_file(f)
        if combined.strip():
            findings = legal_tools.scan_for_slips(combined)
            if findings:
                st.markdown(f"### اكتُشفت {len(findings)} نقطة")
                for fi in findings:
                    ico = {"danger":"🚨","warn":"⚠️","info":"📌"}.get(fi["level"],"📌")
                    lvl=fi["level"]; msg=fi["msg"]; snp=fi["snippet"]
                    st.markdown(f"<div class='alert {lvl}'>{ico} <strong>{msg}</strong><br><small>«{snp}»</small></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='alert ok'>✅ لم تُكتشف زلات صريحة.</div>", unsafe_allow_html=True)
        else:
            st.warning("ارفع ملفاً أو الصق النص.")
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_tool == "doc_analysis":
    st.markdown("## 📁 تحليل المستندات")
    uploaded = st.file_uploader("ارفع الملفات", type=["pdf","docx","txt"], accept_multiple_files=True)
    if uploaded:
        texts = []
        for f in uploaded:
            with st.expander(f"📄 {f.name}"):
                txt = file_processing.extract_text_from_file(f)
                texts.append(txt)
                st.text_area("معاينة", txt[:500]+("..." if len(txt)>500 else ""), height=110, key=f"p_{f.name}")
                facts = legal_tools.extract_quick_facts(txt)
                if facts["dates"]:    st.markdown(f"📅 {' | '.join(facts['dates'])}")
                if facts["amounts"]:  st.markdown(f"💰 {' | '.join(facts['amounts'])}")
                if facts["articles"]: st.markdown(f"⚖️ {' | '.join(facts['articles'])}")
        if st.button("📤 إرسال للمحادثة", use_container_width=False):
            st.session_state.docs_text = texts
            combined = "\n\n---\n\n".join(texts)[:6000]
            st.session_state.pending = (
                "حلّل هذه الوثائق:\n1.الوقائع\n2.نقاط قوة الموظف\n"
                "3.حجج صاحب العمل\n4.التوصية\n\n" + combined
            )
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_tool == "law_search":
    st.markdown("## 📚 البحث في نظام العمل")
    q = st.text_input("ابحث", placeholder="مثال: مكافأة نهاية الخدمة")
    if st.button("🔍 بحث", use_container_width=False) and q.strip():
        st.session_state.pending = f"اذكر المادة ونصها بدقة من نظام العمل السعودي عن: {q}"
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_tool in legal_tools.TOOL_PROMPTS:
    icon, title, auto_prompt = legal_tools.TOOL_PROMPTS[active_tool]
    st.markdown(f"## {icon} {title}")
    context = st.text_area("معطيات القضية (اختياري)", height=110)
    if st.button(f"{icon} تشغيل", use_container_width=False):
        st.session_state.pending = auto_prompt + (f"\n\nمعطيات:\n{context}" if context.strip() else "")
    st.markdown("<hr>", unsafe_allow_html=True)

elif active_tool == "deep_analysis":
    st.markdown("## 🧭 التحليل الشامل — ١٨ محوراً")
    st.caption("يحلل قضيتك من ١٨ زاوية متخصصة وينتهي بإجماع قانوني موحّد.")
    case_text = st.text_area("صف القضية أو الصق وقائعها", height=150,
        placeholder="مثال: نُقلت تعسفياً بعد تقديم شكوى، وتقييمي السلبي صدر من مشرف لم يعمل معي...")
    if not st.session_state.api_key:
        st.markdown("<div class='alert warn'>⚠️ أدخل مفتاح API من «🔌 الاتصال» أولاً.</div>", unsafe_allow_html=True)
    if st.button("🧭 ابدأ التحليل الشامل", use_container_width=False) and case_text.strip():
        if not st.session_state.api_key:
            st.error("أدخل مفتاح API أولاً.")
        else:
            bar = st.progress(0, text="بدء التحليل...")
            emp = st.empty()
            def _upd(i,total,name):
                bar.progress(i/total, text=f"محور {i}/{total}: {name}")
                emp.caption(name)
            with st.spinner("جارٍ التحليل..."):
                result = analysis_engine.run_full_analysis(case_text, ai_call, _upd)
            bar.empty(); emp.empty()
            st.markdown("### ⚖️ رأي الإجماع النهائي")
            st.markdown(f"<div class='card'>{result['consensus'].replace(chr(10),'<br>')}</div>", unsafe_allow_html=True)
            st.markdown("### تفاصيل المحاور")
            for r in result["axes"]:
                with st.expander(f"{r['icon']} {r['name']}"):
                    st.markdown(r["answer"])
    st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# منطقة الدردشة
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.current_sid:
    st.markdown(f"""
    <div style='text-align:center;padding:40px 20px;'>
      <div style='font-size:3rem;'>{'⚖️' if st.session_state.persona=="lawyer" else "🧑"}</div>
      <h2 style='color:{persona_color};margin:10px 0 6px;'>{persona_label}</h2>
      <p style='color:#888;font-size:0.9rem;'>
        {'يصيغ الدعاوى، يكتب المذكرات، ويبني خط الدفاع.' if st.session_state.persona=="lawyer"
         else 'يحسب المستحقات، يحلل المخاطر، ويوجّه نحو القرار الأمثل.'}
      </p>
      <p style='color:#555;font-size:0.82rem;margin-top:16px;'>
        افتح «💬 الجلسات» من الشريط العلوي ← اضغط «➕ جلسة جديدة»
      </p>
    </div>
    """, unsafe_allow_html=True)
else:
    sess = storage.load_session(st.session_state.current_sid)

    hc1, hc2 = st.columns([5,1])
    with hc1:
        nn = st.text_input("", value=sess.get("name","جلسة"),
                           placeholder="اسم الجلسة", label_visibility="collapsed")
        if nn != sess.get("name",""):
            sess["name"] = nn
            sess["messages"] = st.session_state.current_msgs
            storage.save_session(st.session_state.current_sid, sess)
    with hc2:
        if st.button("🗑 مسح", key="clr"):
            st.session_state.current_msgs = []
            sess["messages"] = []
            storage.save_session(st.session_state.current_sid, sess)
            st.rerun()

    ai_cls = "bubble-ai adv" if st.session_state.persona=="advisor" else "bubble-ai"
    html   = "<div class='chat-wrap'>"
    for m in st.session_state.current_msgs:
        body = m["content"].replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
        ts   = m.get("ts","")
        if m["role"]=="user":
            html += f"<div class='bubble-user'>{body}<div class='bubble-meta'>{ts}</div></div>"
        else:
            html += f"<div class='{ai_cls}'>{body}<div class='bubble-meta'>{ts}</div></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    pending    = st.session_state.get("pending","")
    user_input = st.text_area("", value=pending, height=95,
                               placeholder="اكتب سؤالك القانوني هنا...",
                               label_visibility="collapsed", key="inp")
    if pending:
        st.session_state.pending = ""

    with st.container():
        st.markdown("<div class='send-btn'>", unsafe_allow_html=True)
        send = st.button("إرسال ⚡", key="send", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if send and user_input.strip():
        ts = datetime.now().strftime("%H:%M")
        st.session_state.current_msgs.append({"role":"user","content":user_input.strip(),"ts":ts})
        sys_p = legal_tools.PERSONA_PROMPTS[st.session_state.persona]
        if st.session_state.docs_text:
            sys_p += "\n\nالوثائق:\n" + "\n\n".join(st.session_state.docs_text[:3])[:3000]
        with st.spinner("جارٍ التحليل..."):
            resp = ai_call(user_input.strip(), st.session_state.current_msgs[:-1], sys_p)
        st.session_state.current_msgs.append({"role":"assistant","content":resp,"ts":ts})
        sess["messages"] = st.session_state.current_msgs
        sess["persona"]  = st.session_state.persona
        storage.save_session(st.session_state.current_sid, sess)
        st.rerun()
