import streamlit as st
import base64
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
import PyPDF2
import pdfplumber
from docx import Document
import pytesseract
import chromadb
from sentence_transformers import SentenceTransformer
import os
import email
from email import policy
from email.parser import BytesParser

st.set_page_config(page_title="Führer", layout="wide")

def set_background(image_file):
    try:
        with open(image_file, "rb") as f:
            img_data = f.read()
        b64 = base64.b64encode(img_data).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: url(data:image/png;base64,{b64});
                background-size: cover;
                background-attachment: fixed;
            }}
            .stApp, .stMarkdown, .stTitle, .stSubheader, .stTextInput, .stButton, .stFileUploader, .stTabs {{
                background-color: rgba(255, 255, 255, 0.88) !important;
                border-radius: 12px;
                padding: 8px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        return True
    except:
        st.warning("⚠️ الصورة غير موجودة")
        return False

if Path("IMG_5029.png").exists():
    set_background("IMG_5029.png")
else:
    st.warning("⚠️ ارفع الصورة")

st.title("🦾 Führer")
st.markdown("")

@st.cache_resource
def load_embedder():
    return SentenceTransformer('all-MiniLM-L6-v2')

@st.cache_resource
def init_chromadb():
    client = chromadb.PersistentClient(path="./legal_db")
    return client.get_or_create_collection("legal_docs")

embedder = load_embedder()
collection = init_chromadb()

class DocumentIntelligence:
    def extract_text(self, file):
        ext = file.name.split('.')[-1].lower()
        text = ""
        try:
            if ext == "pdf":
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t: text += t + "\n"
                if not text.strip():
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        t = page.extract_text()
                        if t: text += t + "\n"
            elif ext == "docx":
                doc = Document(file)
                for p in doc.paragraphs:
                    text += p.text + "\n"
            elif ext == "txt":
                text = file.read().decode("utf-8")
            elif ext in ["png", "jpg", "jpeg"]:
                img = Image.open(file)
                text = pytesseract.image_to_string(img, lang='ara')
            elif ext == "eml":
                msg = BytesParser(policy=policy.default).parse(file)
                if msg.get_body(preferencelist=('plain', 'html')):
                    text = msg.get_body(preferencelist=('plain', 'html')).get_content()
            else:
                return ""
        except:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    def extract_dates(self, text):
        pattern = r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})'
        matches = re.findall(pattern, text)
        return [f"{m[0]}/{m[1]}/{m[2]}" for m in matches]

    def extract_articles(self, text):
        return re.findall(r'(المادة\s*[\(]?\s*[١٢٣٤٥٦٧٨٩٠]+\s*[\)]?)', text)

class TimelineEngine:
    def build_timeline(self, texts):
        events = []
        parser = DocumentIntelligence()
        for idx, txt in enumerate(texts):
            dates = parser.extract_dates(txt)
            for d in dates:
                try:
                    dt = datetime.strptime(d, '%d/%m/%Y')
                    events.append({"date": dt, "text": txt[:200], "file_index": idx})
                except:
                    pass
        events.sort(key=lambda x: x["date"])
        return events

    def calculate_gaps(self, events):
        gaps = []
        for i in range(len(events)-1):
            diff = (events[i+1]["date"] - events[i]["date"]).days
            if diff > 30:
                gaps.append({
                    "from": events[i]["date"].strftime('%d/%m/%Y'),
                    "to": events[i+1]["date"].strftime('%d/%m/%Y'),
                    "days": diff
                })
        return gaps

class DualAnalyzer:
    def analyze(self, timeline):
        strengths, weaknesses = [], []
        for ev in timeline:
            txt = ev["text"].lower()
            if "أقر" in txt or "اعترف" in txt:
                weaknesses.append("⚠️ اعتراف ضمني")
            if "عذر" in txt or "مرض" in txt:
                strengths.append("✅ أعذار رسمية")
            if "توقيع" not in txt and "ختم" not in txt:
                weaknesses.append("❌ خطاب بدون توقيع")
            if "المادة" in txt:
                strengths.append("📜 استشهاد بمواد")
            if "تهديد" in txt:
                weaknesses.append("⚡ لغة تهديدية")
        return {"strengths": list(set(strengths)), "weaknesses": list(set(weaknesses))}

class PleadingEngine:
    def generate(self, template_type, data):
        templates = {
            "مذكرة دفاع": """
السيد/ رئيس محكمة {court} المحترم،
الموضوع: مذكرة دفاع في الدعوى رقم {case_no}.
نحن {client}، نقدم هذه المذكرة ضد {opponent}، ونبين:
أولاً: الوقائع: {facts}
ثانياً: الدفوع: {defenses}
ثالثاً: الطلبات: {requests}
""",
            "صحيفة دعوى": """
السيد/ رئيس محكمة {court} المحترم،
الموضوع: صحيفة دعوى من {client} ضد {opponent}.
الوقائع: {facts}
الأسباب: {defenses}
الطلبات: {requests}
""",
            "عريضة اعتراض": """
السيد/ رئيس محكمة {court} المحترم،
الموضوع: اعتراض على القرار رقم {case_no}.
أسباب الاعتراض: {defenses}
الطلبات: {requests}
"""
        }
        return templates.get(template_type, "قالب غير موجود").format(**data)

def detect_contradictions(texts):
    contradictions = []
    for idx, txt in enumerate(texts):
        dates = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', txt)
        if len(dates) >= 2 and dates[0] == dates[1]:
            contradictions.append(f"تناقض في التواريخ بالملف {idx+1}")
    return contradictions

def analyze_style(texts):
    return sum(1 for t in texts if "تهديد" in t or "فوراً" in t)

def calculate_deadlines(events):
    results = []
    for ev in events:
        if "فصل" in ev["text"] or "إنهاء" in ev["text"]:
            deadline = ev["date"] + timedelta(days=365)
            results.append({"event": ev["text"][:50], "deadline": deadline.strftime('%d/%m/%Y')})
    return results

def calculate_risk(timeline, gaps, contradictions, style_score):
    risk = len(gaps) * 2 + len(contradictions) * 5 + style_score
    if len(timeline) < 2: risk += 10
    return min(risk, 100)

def credibility_score(texts):
    score = 100
    for t in texts:
        if "نحن نؤكد" in t: score -= 5
        if "مادة" in t and "خطأ" in t: score -= 10
    return max(score, 0)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📚 رفع الملفات", "🔎 البحث", "📊 الجدول الزمني", "⚖️ التحليل", "📄 التقارير"])
uploaded_files = []

with tab1:
    st.subheader("رفع الملفات")
    uploaded = st.file_uploader("اختر الملفات", type=["pdf","docx","txt","png","jpg","jpeg","eml"], accept_multiple_files=True)
    if uploaded:
        uploaded_files = uploaded
        if st.button("فهرسة"):
            parser = DocumentIntelligence()
            total = 0
            for f in uploaded_files:
                text = parser.extract_text(f)
                if text:
                    chunks = [text[i:i+800] for i in range(0, len(text), 800)]
                    for i, chunk in enumerate(chunks):
                        emb = embedder.encode(chunk).tolist()
                        collection.add(documents=[chunk], embeddings=[emb], ids=[f"{f.name}_{i}"])
                    total += len(chunks)
            st.success(f"تم فهرسة {total} قطعة")

with tab2:
    st.subheader("البحث الدلالي")
    query = st.text_input("اسأل")
    if query:
        q_emb = embedder.encode(query).tolist()
        results = collection.query(query_embeddings=[q_emb], n_results=5)
        if results['documents']:
            for r in results['documents'][0]:
                st.write(f"- {r[:500]}...")

with tab3:
    st.subheader("الجدول الزمني")
    if uploaded_files:
        parser = DocumentIntelligence()
        texts = [parser.extract_text(f) for f in uploaded_files]
        engine = TimelineEngine()
        timeline = engine.build_timeline(texts)
        gaps = engine.calculate_gaps(timeline)
        for ev in timeline:
            st.write(f"- {ev['date'].strftime('%d/%m/%Y')}: {ev['text'][:100]}...")
        if gaps:
            for g in gaps:
                st.warning(f"فجوة {g['days']} يوم من {g['from']} إلى {g['to']}")

with tab4:
    st.subheader("نقاط القوة والضعف")
    if uploaded_files:
        parser = DocumentIntelligence()
        texts = [parser.extract_text(f) for f in uploaded_files]
        engine = TimelineEngine()
        timeline = engine.build_timeline(texts)
        gaps = engine.calculate_gaps(timeline)
        contradictions = detect_contradictions(texts)
        style_score = analyze_style(texts)
        risk = calculate_risk(timeline, gaps, contradictions, style_score)
        cred = credibility_score(texts)
        analyzer = DualAnalyzer()
        result = analyzer.analyze(timeline)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("الخطورة", f"{risk}/100")
            st.metric("مصداقية الخصم", f"{cred}/100")
        with col2:
            st.metric("التناقضات", len(contradictions))
            st.metric("التصعيد", style_score)
        
        for s in result["strengths"]: st.success(s)
        for w in result["weaknesses"]: st.error(w)

with tab5:
    st.subheader("التقارير واللوائح")
    if st.button("تقرير كامل"):
        parser = DocumentIntelligence()
        texts = [parser.extract_text(f) for f in uploaded_files]
        engine = TimelineEngine()
        timeline = engine.build_timeline(texts)
        gaps = engine.calculate_gaps(timeline)
        contradictions = detect_contradictions(texts)
        style_score = analyze_style(texts)
        deadlines = calculate_deadlines(timeline)
        risk = calculate_risk(timeline, gaps, contradictions, style_score)
        cred = credibility_score(texts)
        report = f"الخطورة: {risk}\nالمصداقية: {cred}\nالتناقضات: {len(contradictions)}\nالفجوات: {len(gaps)}\n"
        for d in deadlines: report += f"\n- {d['event']} → {d['deadline']}"
        st.download_button("تحميل", data=report, file_name="تقرير.txt")
    
    template = st.selectbox("نوع اللائحة", ["مذكرة دفاع", "صحيفة دعوى", "عريضة اعتراض"])
    if st.button("أنشئ"):
        data = {"court": "المحكمة", "case_no": "قيد التحليل", "client": "الطرف الأول", "opponent": "الخصم", "facts": "الوقائع المستخلصة", "defenses": "نقاط الدفاع", "requests": "الطلبات"}
        engine = PleadingEngine()
        st.text_area("المسودة", engine.generate(template, data), height=300)