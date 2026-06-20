import streamlit as st
import base64
import re
import tempfile
from datetime import datetime, timedelta
from PIL import Image
import PyPDF2
import pdfplumber
from docx import Document
import pytesseract
import chromadb
from sentence_transformers import SentenceTransformer
import email
from email import policy
from email.parser import BytesParser
from transformers import pipeline

st.set_page_config(page_title="Führer", layout="wide")

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

    def extract_ambiguous(self, text):
        phrases = ["يحق للجهة", "ما تراه مناسباً", "وفق الإجراءات النظامية", "حسب المصلحة", "تقدير الجهة", "لجنة مختصة", "سيتم الرد لاحقاً", "نحن نؤكد", "كما تعلمون"]
        return [p for p in phrases if p in text]

    def extract_claims(self, text):
        claims = []
        patterns = [r'ثبت لدينا', r'نستدل من', r'بناءً على ما ورد', r'نشير إلى', r'نلفت انتباهكم']
        for p in patterns:
            if re.search(p, text):
                claims.append(p)
        return claims

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

class RuleEngine:
    def __init__(self):
        self.rules = [
            {"cond": "days_abandoned > 30", "out": "⚠️ مدة الانقطاع تجاوزت 30 يوماً (ترك عمل)"},
            {"cond": "days_abandoned > 15 and days_abandoned <= 30", "out": "⚠️ مدة الانقطاع 15-30 يوماً (إنذار)"},
            {"cond": "days_since_firing > 365", "out": "⛔ مضي أكثر من سنة على الفصل (سقوط حق التقاضي)"},
            {"cond": "days_since_firing > 180 and days_since_firing <= 365", "out": "⏳ مضي أكثر من 6 أشهر على الفصل (تقادم جزئي)"},
            {"cond": "reply_delay > 30", "out": "⏳ تأخير إداري من الخصم (أكثر من 30 يوماً)"},
            {"cond": "reply_delay > 15 and reply_delay <= 30", "out": "⏳ تأخير إداري متوسط (15-30 يوماً)"},
            {"cond": "ambiguous_phrases > 3", "out": "🔍 عبارات غامضة في خطابات الخصم (طعن محتمل)"},
            {"cond": "ambiguous_phrases > 5", "out": "🔍 عبارات غامضة كثيرة (تعسف)"},
            {"cond": "contradictions > 1", "out": "⚡ تناقض داخلي في مراسلات الخصم"},
            {"cond": "contradictions > 3", "out": "⚡ تناقضات متعددة (فقدان المصداقية)"},
            {"cond": "force_majeure is False and missed_deadline is True", "out": "📌 فاتك موعد نظامي دون عذر قاهر"},
            {"cond": "settlement_offer is True and risk_score > 60", "out": "🤝 الصلح أفضل من الاستمرار"},
            {"cond": "settlement_offer is True and risk_score <= 40", "out": "⚖️ الصلح ممكن لكن القضية قوية"},
            {"cond": "court_grade == 'Supreme' and similarity > 0.8", "out": "⭐ حكم مشابه من المحكمة العليا (وزن استدلالي عالٍ)"},
            {"cond": "court_grade == 'Appeal' and similarity > 0.7", "out": "📜 حكم من محكمة الاستئناف مشابه"},
            {"cond": "court_grade == 'First' and similarity > 0.6", "out": "📄 حكم من محكمة الدرجة الأولى مشابه"},
            {"cond": "force_majeure is True and days_abandoned > 60", "out": "📌 عذر قاهر يبرر الانقطاع الطويل"},
            {"cond": "service_length < 2", "out": "📌 مدة الخدمة أقل من سنتين (مكافأة نصف شهر)"},
            {"cond": "service_length >= 2 and service_length < 5", "out": "📌 مدة الخدمة 2-5 سنوات (مكافأة شهرين)"},
            {"cond": "service_length >= 5", "out": "📌 مدة الخدمة أكثر من 5 سنوات (مكافأة كاملة)"},
            {"cond": "absence_days > 15 and absence_days <= 20", "out": "⚠️ غياب 15-20 يوماً (إنذار أول)"},
            {"cond": "absence_days > 20 and absence_days <= 30", "out": "⚠️ غياب 20-30 يوماً (إنذار ثانٍ)"},
            {"cond": "absence_days > 30", "out": "⚠️ غياب أكثر من 30 يوماً (فصل)"},
            {"cond": "no_investigation_before_firing", "out": "⚖️ فصل بدون تحقيق (بطلان القرار)"},
            {"cond": "notification_after_7_days", "out": "⚖️ تبليغ بعد 7 أيام (إخلال إجرائي)"},
            {"cond": "not_registered_letter", "out": "⚖️ تبليغ بكتاب غير مسجل (عدم العلم)"},
            {"cond": "violation_date_not_specified", "out": "⚖️ عدم تحديد تاريخ المخالفة (غموض يفسر لصالحك)"},
            {"cond": "penalty_after_1_year", "out": "⛔ مضى سنة على المخالفة دون عقوبة (سقوط الحق)"},
            {"cond": "no_appeal_period_specified", "out": "⚖️ عدم تحديد مدة التظلم (لك الاعتراض في أي وقت)"},
            {"cond": "expert_request_rejected", "out": "⚖️ رفض طلب الخبرة (إخلال بحق الدفاع)"},
            {"cond": "judgment_without_hearing", "out": "⚖️ حكم دون سماع أقوالك (بطلان)"},
            {"cond": "documents_not_submitted_within_5_days", "out": "⚖️ تأخر تقديم المستندات (لا يؤثر على أصل الحق)"},
            {"cond": "no_response_after_90_days", "out": "⚖️ مضى 90 يوماً على طلبك دون رد (اعتبار موافقة ضمنية)"},
            {"cond": "new_evidence_after_deadline", "out": "📌 مستندات جديدة بعد الميعاد (تُقبل لتعلق بالنظام العام)"},
            {"cond": "opponent_refuses_to_produce_document", "out": "⚖️ امتناع الخصم عن تقديم مستند تحت يده (يُحكم ضده)"},
            {"cond": "document_not_signed", "out": "⚖️ مستند غير موقع (لا حجية له)"},
            {"cond": "document_unsigned_copy", "out": "⚖️ صورة غير مصدقة (لا يُعتد بها)"},
            {"cond": "forgery_proven", "out": "⚖️ تزوير ثبت (جريمة)"},
            {"cond": "witness_testimony_accepted", "out": "📌 شهادة شهود مقبولة (إن كانت جائزة)"},
            {"cond": "witnesses_contradictory", "out": "⚖️ تناقض شهادات الشهود (تُرجح أقوال الأكثر عدالة)"},
            {"cond": "witness_relative_of_opponent", "out": "⚖️ شاهد قريب للخصم (شهادته مردودة)"},
            {"cond": "witness_old_event", "out": "⚖️ شهادة عن واقعة قديمة (لا تُقبل للتقادم)"},
            {"cond": "witness_absent_without_excuse", "out": "⚖️ غياب الشاهد دون عذر (يُغرّم)"},
            {"cond": "two_witnesses_vs_one", "out": "📌 شاهدين ضد واحد (تُقبل شهادتهما)"},
            {"cond": "digital_evidence_not_secure", "out": "⚖️ دليل رقمي غير مؤمن (لا حجية له)"},
            {"cond": "non_judicial_acknowledgment", "out": "📌 إقرار غير قضائي (حجة على المقر)"},
            {"cond": "repeated_threats", "out": "⚖️ تكرار التهديد من الخصم (تعسف)"},
            {"cond": "unlimited_deadline_request", "out": "⚖️ طلب مهلة غير محددة (مماطلة)"},
            {"cond": "single_response_to_multiple_requests", "out": "⚖️ رد واحد على عدة طلبات (تغييب للحقائق)"},
            {"cond": "referral_to_another_reference", "out": "⚖️ إحالة لمرجع آخر (دوران إداري)"},
            {"cond": "irrelevant_document_request", "out": "⚖️ طلب مستندات غير ذات صلة (مناورة)"},
            {"cond": "unsigned_meeting_minutes", "out": "⚖️ محضر اجتماع غير موقع (عدم اعتراف)"},
            {"cond": "vague_language_in_letter", "out": "⚖️ لغة غامضة في خطاب الخصم (طعن محتمل)"},
            {"cond": "apology_without_correction", "out": "⚖️ اعتذار دون تصحيح (لا قيمة قانونية له)"},
            {"cond": "study_promise_without_action", "out": "⚖️ وعد بالدراسة دون إجراء (تسويف)"},
            {"cond": "meeting_without_agenda", "out": "⚖️ اجتماع دون جدول أعمال (غير جاد)"},
            {"cond": "representative_without_authority", "out": "⚖️ حضور مندوب دون صفة (عدم صفة)"},
            {"cond": "letter_sent_after_working_hours", "out": "⚖️ إرسال خطاب بعد الدوام (يُحتسب في اليوم التالي)"},
            {"cond": "supreme_court_ruling", "out": "⭐ حكم من المحكمة العليا (أقوى وزن استدلالي)"},
            {"cond": "appeal_court_ruling", "out": "📜 حكم من محكمة الاستئناف (وزن متوسط)"},
            {"cond": "first_instance_ruling", "out": "📄 حكم من محكمة الدرجة الأولى (وزن أقل)"},
            {"cond": "recent_ruling", "out": "📌 حكم حديث (خلال سنة) (وزن أعلى)"},
            {"cond": "old_ruling", "out": "📌 حكم قديم (أكثر من 10 سنوات) (وزن أقل)"},
            {"cond": "high_similarity_ruling", "out": "⭐ سابقة مباشرة (تشابه 90% فما فوق)"},
            {"cond": "medium_similarity_ruling", "out": "📌 مؤشر (تشابه 50-90%)"},
            {"cond": "specialized_circuit_ruling", "out": "⭐ حكم من دائرة متخصصة (وزن خاص)"},
            {"cond": "unanimous_ruling", "out": "⭐ حكم بالإجماع (وزن أقوى)"},
            {"cond": "majority_ruling", "out": "📌 حكم بأغلبية (وزن أقل)"},
            {"cond": "settlement_offered_before_decision", "out": "📌 عرض صلح قبل القرار (مؤشر حسن نية)"},
            {"cond": "rejected_settlement_without_reason", "out": "⚖️ رفض الصلح دون مبرر (تعنت)"},
            {"cond": "offered_settlement_and_refused", "out": "📌 عرضت صلح ورفض (يحق لك التعويض)"},
            {"cond": "government_settlement", "out": "📌 صلح مع جهة حكومية (إجراء شكلي)"},
            {"cond": "both_parties_agree_settlement", "out": "✅ اتفاق صلح نهائي"},
            {"cond": "settlement_partial_right", "out": "📌 تنازل عن جزء من الحق (يُحتسب)"},
            {"cond": "settlement_meeting_absence", "out": "⚖️ غياب الخصم عن جلسة الصلح (إنذار)"},
            {"cond": "settlement_deadline_request", "out": "📌 طلب مهلة للصلح (تُمنح مهلة معقولة)"},
            {"cond": "settlement_out_of_court", "out": "📌 صلح خارج المحكمة (يُصدق عليه)"},
            {"cond": "settlement_broken", "out": "⚖️ نقض الصلح (يُلزم بالتعويض)"},
            {"cond": "arbitrary_dismissal", "out": "⚖️ فصل تعسفي (تستحق تعويضاً)"},
            {"cond": "violation_not_proven", "out": "⚖️ عدم ثبوت المخالفة (يُلغى الفصل)"},
            {"cond": "salary_delay_proven", "out": "⚖️ تأخير الرواتب (تستحق تعويضاً)"},
            {"cond": "end_of_service_benefit_not_paid", "out": "⚖️ عدم صرف المكافأة (تطالب بها)"},
            {"cond": "unlawful_deduction", "out": "⚖️ خصم من الراتب بغير حق (يُرد لك)"},
            {"cond": "disproportionate_fine", "out": "⚖️ غرامة غير متناسبة (تُخفض)"},
            {"cond": "fine_not_specified_in_contract", "out": "⚖️ غرامة غير محددة في العقد (لا تُوقع)"},
            {"cond": "repeated_violation", "out": "⚖️ تكرار المخالفة (يجوز مضاعفة الغرامة)"},
            {"cond": "fine_contrary_to_regulations", "out": "⚖️ غرامة مخالفة للنظام (تُلغى)"},
            {"cond": "undefined_compensation", "out": "⚖️ تعويض غير محدد (يُقدر بقيمة الضرر)"},
            {"cond": "proven_illness", "out": "📌 إعاقة صحية (عذر مقبول)"},
            {"cond": "weather_conditions_prevent_attendance", "out": "📌 ظروف جوية تمنع الحضور (عذر قاهر)"},
            {"cond": "death_of_relative", "out": "📌 وفاة قريب (إجازة رسمية)"},
            {"cond": "emergency_accident", "out": "📌 حادث طارئ (عذر مقبول)"},
            {"cond": "authority_closed", "out": "📌 إغلاق الجهة (عذر قاهر)"},
            {"cond": "service_disruption", "out": "📌 انقطاع الخدمات (عذر قاهر)"},
            {"cond": "lawyer_communication_failure", "out": "📌 تعذر التواصل مع المحامي (عذر مقبول)"},
            {"cond": "strikes", "out": "📌 إضرابات (عذر قاهر)"},
            {"cond": "administrative_order_preventing_attendance", "out": "📌 قرار إداري يمنع الحضور (عذر مقبول)"},
            {"cond": "epidemic", "out": "📌 وباء (عذر قاهر)"},
            {"cond": "electronic_communication_failure", "out": "📌 تعطل الاتصال الإلكتروني (عذر مقبول)"},
            {"cond": "natural_disaster", "out": "📌 كارثة طبيعية (عذر قاهر)"},
            {"cond": "travel_ban", "out": "📌 منع السفر (عذر قاهر)"},
            {"cond": "health_quarantine", "out": "📌 حجر صحي (عذر قاهر)"},
            {"cond": "fire_or_flood", "out": "📌 حريق أو فيضان (عذر قاهر)"},
            {"cond": "political_unrest", "out": "📌 اضطرابات سياسية (عذر قاهر)"},
            {"cond": "absence_of_legal_representative", "out": "📌 غياب الممثل القانوني (عذر مقبول)"},
            {"cond": "court_closure", "out": "📌 إغلاق المحكمة (عذر قاهر)"}
        ]

    def apply(self, data):
        alerts = []
        for r in self.rules:
            try:
                if eval(r["cond"]):
                    alerts.append(r["out"])
            except:
                pass
        return alerts

class DualAnalyzer:
    def analyze(self, timeline):
        strengths, weaknesses = [], []
        for ev in timeline:
            txt = ev["text"].lower()
            if "أقر" in txt or "اعترف" in txt:
                weaknesses.append("اعتراف ضمني")
            if "عذر" in txt or "مرض" in txt or "ظروف" in txt:
                strengths.append("أعذار رسمية")
            if "توقيع" not in txt and "ختم" not in txt:
                weaknesses.append("خطاب بدون توقيع")
            if "المادة" in txt:
                strengths.append("استشهاد بمواد نظامية")
            if "تهديد" in txt or "فوراً" in txt:
                weaknesses.append("لغة تهديدية")
            if "نحن نؤكد" in txt:
                weaknesses.append("تأكيد دون مستند")
            if "نحن نعلم" in txt:
                strengths.append("إقرار بالعلم")
            if "نحن نرفض" in txt:
                strengths.append("موقف حازم")
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
        if "مادة" in txt and "مادة" in txt and "خطأ" in txt:
            contradictions.append(f"خطأ في إشارة لمادة بالملف {idx+1}")
        if "توقيع" not in txt and "ختم" in txt:
            contradictions.append(f"ختم بدون توقيع بالملف {idx+1}")
    return contradictions

def analyze_style(texts):
    score = 0
    for t in texts:
        if "تهديد" in t or "فوراً" in t or "يجب" in t:
            score += 1
        if "نرجو" in t or "نأمل" in t:
            score -= 1
        if "عاجل" in t:
            score += 2
    return max(score, 0)

def calculate_deadlines(events):
    results = []
    for ev in events:
        if "فصل" in ev["text"] or "إنهاء" in ev["text"] or "إيقاف" in ev["text"]:
            deadline = ev["date"] + timedelta(days=365)
            results.append({"event": ev["text"][:50], "deadline": deadline.strftime('%d/%m/%Y')})
        if "اعتراض" in ev["text"]:
            deadline = ev["date"] + timedelta(days=30)
            results.append({"event": ev["text"][:50], "deadline": deadline.strftime('%d/%m/%Y')})
        if "استئناف" in ev["text"]:
            deadline = ev["date"] + timedelta(days=60)
            results.append({"event": ev["text"][:50], "deadline": deadline.strftime('%d/%m/%Y')})
    return results

def calculate_risk(timeline, gaps, contradictions, style_score):
    risk = len(gaps) * 2 + len(contradictions) * 5 + style_score
    if len(timeline) < 2:
        risk += 10
    if len(timeline) > 10:
        risk -= 5
    return min(max(risk, 0), 100)

def credibility_score(texts):
    score = 100
    for t in texts:
        if "نحن نؤكد" in t:
            score -= 5
        if "مادة" in t and "خطأ" in t:
            score -= 10
        if "كما سبق" in t:
            score -= 3
        if "نحن نعتقد" in t:
            score -= 2
        if "نحن على يقين" in t:
            score -= 4
    return max(score, 0)

def extract_fact_summary(timeline):
    if not timeline:
        return "لا توجد وقائع كافية."
    summary = "تسلسل الأحداث الرئيسية:\n"
    for ev in timeline[:5]:
        summary += f"- {ev['date'].strftime('%d/%m/%Y')}: {ev['text'][:100]}...\n"
    return summary

def extract_party_names(texts):
    parties = []
    for t in texts:
        for p in ["المدعي", "المدعى عليه", "الهيئة", "الشركة", "المؤسسة", "الموظف", "العامل", "الوكيل", "المحامي"]:
            if p in t:
                parties.append(p)
    return list(set(parties)) if parties else ["أطراف غير محددة"]

def generate_strategy(timeline, gaps, contradictions, risk):
    strategy = []
    if gaps:
        strategy.append("استغل الفجوات الزمنية كدليل على تعنت الخصم.")
    if contradictions:
        strategy.append("قدم التناقضات المكتشفة كطعن على مصداقية الخصم.")
    if risk > 70:
        strategy.append("الخطر مرتفع، يوصى بالاستعداد للتصعيد القضائي.")
    elif risk > 50:
        strategy.append("خطر متوسط، يوصى بالتفاوض مع الاحتفاظ بالخيارات القضائية.")
    else:
        strategy.append("خطر منخفض، يمكن المضي قدماً في الإجراءات الحالية.")
    if not gaps and not contradictions and risk < 40:
        strategy.append("الوضع مستقر، يمكن الاستمرار بالوتيرة الحالية.")
    if len(gaps) > 3:
        strategy.append("فجوات متعددة، يوصى بتقديم شكوى إدارية ضد تعنت الخصم.")
    return "\n".join(strategy)

def extract_evidence_gaps(texts, claims):
    gaps = []
    for claim in claims:
        found = False
        for t in texts:
            if claim in t:
                found = True
                break
        if not found:
            gaps.append(claim)
    return gaps

def procedural_pattern_analyzer(timeline):
    if len(timeline) < 2:
        return "لا توجد بيانات كافية لتحليل النمط."
    weekdays = [ev["date"].weekday() for ev in timeline]
    if all(w in [4, 5] for w in weekdays):
        return "الخصم يرد في نهاية الأسبوع (مماطلة متعمدة)."
    hours = [ev["date"].hour for ev in timeline]
    if all(h > 15 for h in hours):
        return "الخصم يرد في ساعات متأخرة (محاولة لتعطيل الرد)."
    return "لا نمط محدد، إجراءات عادية."

def settlement_calculator(risk, credibility, contradictions):
    if risk > 70:
        return "فرصة الصلح منخفضة (الخصم متصلب)."
    elif risk < 30 and credibility > 70 and contradictions == 0:
        return "فرصة الصلح عالية، يوصى بالتقدم بعرض."
    else:
        return "فرصة الصلح متوسطة، يحتاج تقييم إضافي."

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📚 الملفات", "🔎 البحث", "📊 الجدول الزمني", "⚖️ التحليل الثنائي", "📄 التقارير", "🧠 الاستراتيجية", "⚙️ الأدوات المتقدمة", "🤖 Hugging Face"
])

uploaded_files = []

with tab1:
    st.subheader("رفع الملفات")
    uploaded = st.file_uploader("اختر الملفات", type=["pdf","docx","txt","png","jpg","jpeg","eml"], accept_multiple_files=True)
    if uploaded:
        uploaded_files = uploaded
        if st.button("فهرسة وتحليل"):
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
    st.subheader("البحث الدلالي في الملفات المفهرسة")
    query = st.text_input("اكتب سؤالك أو كلمتك المفتاحية")
    if query:
        q_emb = embedder.encode(query).tolist()
        results = collection.query(query_embeddings=[q_emb], n_results=5)
        if results['documents']:
            for r in results['documents'][0]:
                st.write(f"- {r[:500]}...")

with tab3:
    st.subheader("الجدول الزمني والفجوات")
    if uploaded_files:
        parser = DocumentIntelligence()
        texts = [parser.extract_text(f) for f in uploaded_files]
        engine = TimelineEngine()
        timeline = engine.build_timeline(texts)
        gaps = engine.calculate_gaps(timeline)
        st.markdown("**الأحداث مرتبة زمنياً:**")
        for ev in timeline:
            st.write(f"- {ev['date'].strftime('%d/%m/%Y')}: {ev['text'][:100]}...")
        if gaps:
            st.warning("**الفجوات الزمنية (تجاوز 30 يوماً):**")
            for g in gaps:
                st.write(f"من {g['from']} إلى {g['to']} = {g['days']} يوماً")
        else:
            st.success("لا توجد فجوات زمنية ملحوظة.")

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
            st.metric("مؤشر الخطورة", f"{risk}/100")
            st.metric("مصداقية الخصم", f"{cred}/100")
        with col2:
            st.metric("عدد التناقضات", len(contradictions))
            st.metric("درجة التصعيد", style_score)
        
        st.markdown("**🟢 نقاط قوتك:**")
        for s in result["strengths"]:
            st.success(s)
        st.markdown("**🔴 نقاط ضعفك:**")
        for w in result["weaknesses"]:
            st.error(w)

with tab5:
    st.subheader("التقارير واللوائح")
    if uploaded_files and st.button("توليد تقرير كامل"):
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
        facts = extract_fact_summary(timeline)
        parties = extract_party_names(texts)
        
        report = f"""
تقرير Führer الشامل
===================
التاريخ: {datetime.now().strftime('%d/%m/%Y')}
عدد الملفات: {len(uploaded_files)}
الأطراف: {', '.join(parties)}
مؤشر الخطورة: {risk}/100
مصداقية الخصم: {cred}/100
عدد التناقضات: {len(contradictions)}
درجة التصعيد: {style_score}
عدد الفجوات الزمنية: {len(gaps)}

الوقائع المستخلصة:
{facts}

المواعيد النهائية:
"""
        for d in deadlines:
            report += f"\n- {d['event']} → {d['deadline']}"
        st.download_button("تحميل التقرير", data=report, file_name="تقرير_Führer.txt")
    
    st.subheader("صياغة لائحة")
    template = st.selectbox("اختر نوع اللائحة", ["مذكرة دفاع", "صحيفة دعوى", "عريضة اعتراض"])
    if uploaded_files and st.button("أنشئ مسودة"):
        parser = DocumentIntelligence()
        texts = [parser.extract_text(f) for f in uploaded_files]
        engine = TimelineEngine()
        timeline = engine.build_timeline(texts)
        facts = extract_fact_summary(timeline)
        parties = extract_party_names(texts)
        analyzer = DualAnalyzer()
        result = analyzer.analyze(timeline)
        defenses = "\n".join(result["strengths"]) if result["strengths"] else "سيتم تحديد الدفوع لاحقاً"
        data = {
            "court": "محكمة العمل/ديوان المظالم",
            "case_no": "قيد التحليل",
            "client": parties[0] if parties else "الطرف الأول",
            "opponent": parties[1] if len(parties) > 1 else "الجهة الخصمة",
            "facts": facts,
            "defenses": defenses,
            "requests": "إلغاء القرار الصادر ضدنا، وإلزام الخصم بالتعويض"
        }
        engine = PleadingEngine()
        draft = engine.generate(template, data)
        st.text_area("المسودة (قابلة للتعديل)", draft, height=300)

with tab6:
    st.subheader("الاستراتيجية المقترحة")
    if uploaded_files:
        parser = DocumentIntelligence()
        texts = [parser.extract_text(f) for f in uploaded_files]
        engine = TimelineEngine()
        timeline = engine.build_timeline(texts)
        gaps = engine.calculate_gaps(timeline)
        contradictions = detect_contradictions(texts)
        style_score = analyze_style(texts)
        risk = calculate_risk(timeline, gaps, contradictions, style_score)
        strategy = generate_strategy(timeline, gaps, contradictions, risk)
        st.markdown(strategy)

with tab7:
    st.subheader("الأدوات المتقدمة")
    if uploaded_files:
        parser = DocumentIntelligence()
        texts = [parser.extract_text(f) for f in uploaded_files]
        timeline = TimelineEngine().build_timeline(texts)
        gaps = TimelineEngine().calculate_gaps(timeline)
        contradictions = detect_contradictions(texts)
        cred = credibility_score(texts)
        risk = calculate_risk(timeline, gaps, contradictions, analyze_style(texts))
        
        st.markdown("**نقاط القرار الحرجة:**")
        for ev in timeline:
            if "فصل" in ev["text"] or "إيقاف" in ev["text"] or "اعتراض" in ev["text"]:
                st.warning(f"- {ev['date'].strftime('%d/%m/%Y')}: {ev['text'][:100]}...")
        
        st.markdown("**تكتيك الخصم الزمني:**")
        pattern = procedural_pattern_analyzer(timeline)
        st.info(pattern)
        
        st.markdown("**حاسبة فرص الصلح:**")
        settlement = settlement_calculator(risk, cred, len(contradictions))
        st.info(settlement)
        
        st.markdown("**فجوات الأدلة (ادعاءات غير مدعومة):**")
        claims = []
        for t in texts:
            claims.extend(DocumentIntelligence().extract_claims(t))
        gaps_evidence = extract_evidence_gaps(texts, claims)
        if gaps_evidence:
            for g in gaps_evidence:
                st.error(f"- {g}")
        else:
            st.success("جميع الادعاءات مدعومة بمستندات.")

with tab8:
    st.subheader("Hugging Face – أي نموذج تختاره")
    model_name = st.text_input("أدخل اسم النموذج من Hugging Face", value="faisalaljahlan/Labour-Law-SA-QA")
    
    @st.cache_resource
    def load_hf_model(name):
        return pipeline("text-generation", model=name)
    
    if st.button("تحميل النموذج"):
        with st.spinner("جاري تحميل النموذج..."):
            pipe = load_hf_model(model_name)
            st.session_state["hf_pipe"] = pipe
            st.success("تم التحميل.")
    
    prompt = st.text_area("أدخل النص أو السؤال")
    if st.button("تشغيل النموذج") and "hf_pipe" in st.session_state:
        result = st.session_state["hf_pipe"](prompt, max_new_tokens=200)
        st.write(result[0]['generated_text'])