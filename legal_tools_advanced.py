# legal_tools_advanced.py
"""
أدوات قانونية متقدمة للتطبيق القانوني (Führer).
يشمل: تصنيف آلي، بحث قانوني، تفنيد قانوني، توليد مستندات.
"""

import re
import json
from typing import List, Dict, Optional, Callable, Tuple
from datetime import datetime
from docx import Document
from io import BytesIO
from legal_database import get_legal_database

# ============ 1. نظام تصنيف آلي للقضايا ============
class LegalCaseClassifier:
    """نظام تصنيف آلي لقضايا القانون العمالي باستخدام كلمات رئيسية"""
    def __init__(self):
        self.db = get_legal_database()
        self.keywords = {
            "نهاية الخدمة": ["نهاية خدمة", "مكافأة نهاية خدمة", "استقالة", "فصل", "مادة 84"],
            "الأجور": ["راتب", "أجر", "زيادة", "خصم", "مستحقات", "مادة 90"],
            "عقد العمل": ["عقد", "عقد عمل", "تجديد", "مدة", "مادة 78"],
            "ساعات العمل": ["ساعات", "عمل إضافي", "فترة راحة", "مادة 47"],
            "التأمينات الاجتماعية": ["تأمينات", "GOSI", "معاش", "مادة 130"],
            "المنازعات العمالية": ["منازعة", "دعوى", "محاكمة", "مادة 140"],
            "السلامة المهنية": ["سلامة", "مخاطر", "حماية", "مادة 120"],
            "الإجازات": ["إجازة", "إجازة سنوية", "مادة 53"],
            "التأديب": ["تأديب", "إنذار", "عقوبة"],
            "الترقيات": ["ترقية", "زيادة راتب", "تطوير"],
        }

    def classify(self, text: str) -> Tuple[str, float, List[str]]:
        """تصنيف نص قضية إلى فئة قانونية."""
        text_lower = text.lower()
        scores = {}
        for category, keywords in self.keywords.items():
            matched = [kw for kw in keywords if kw in text_lower]
            if matched:
                scores[category] = len(matched) / len(keywords)
        if not scores:
            return "عام", 0.0, []
        best_category = max(scores.items(), key=lambda x: x[1])
        return best_category[0], best_category[1], self.keywords[best_category[0]]

    def classify_with_ai(self, text: str, call_ai_fn: Callable) -> str:
        """تصنيف باستخدام AI لزيادة الدقة"""
        prompt = f"""
        أنت خبير في القانون العمالي السعودي.
        صنف النص التالي إلى إحدى الفئات التالية:
        {', '.join(self.keywords.keys())}
        النص:
        {text}
        يجب أن تكون الفئة واحدة من الفئات المذكورة أعلاه فقط.
        اجعل إجابتك كلمة واحدة فقط: الفئة.
        """
        try:
            category = call_ai_fn(prompt, [], "صنف إلى فئة قانونية واحدة.")
            category = category.strip().split()[0]
            if category in self.keywords:
                return category
            return "عام"
        except:
            return "عام"

# ============ 2. محرك بحث قانوني ============
class LegalSearchEngine:
    """محرك بحث قانوني في نصوص القانون العمالي السعودي"""
    def __init__(self):
        self.db = get_legal_database()

    def search(self, query: str, category: Optional[str] = None, max_results: int = 10) -> List[Dict]:
        """بحث في قاعدة البيانات القانونية."""
        local_results = self.db.search_laws(query, category)
        results = []
        query_lower = query.lower()
        for law in local_results:
            text = law.get("text", "").lower()
            matches = len(re.findall(re.escape(query_lower), text))
            score = min(1.0, matches / 5)
            results.append({
                "id": law.get("article", "unknown"),
                "title": law.get("title", "بدون عنوان"),
                "text": law.get("text", ""),
                "source": law.get("source", "مجهول"),
                "category": law.get("category", "عام"),
                "score": score,
                "type": "law"
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

# ============ 3. أداة تفنيد قانوني ============
class LegalRebuttalGenerator:
    """توليد تفنيد قانوني آلي للادعاءات"""
    def __init__(self):
        self.db = get_legal_database()

    def generate(self, claim: str, case_details: str, call_ai_fn: Callable) -> Dict:
        """توليد تفنيد قانوني للادعاء."""
        prompt = f"""
        أنت محامي سعودي خبير بالقانون العمالي، ولديك 20 عاماً من الخبرة.
        الادعاء:
        {claim}
        تفاصيل القضية:
        {case_details}
        قم بتوليد تفنيد قانوني مفصل يعارض الادعاء، مع:
        1. تحليل الادعاء
        2. المواد القانونية الداعمة
        3. حجج دفاعية قوية
        4. استنتاج قانوني واضح
        يجب أن يكون التفنيد دقيقاً قانونياً ومستنداً إلى نصوص قانونية حقيقية.
        """
        try:
            response = call_ai_fn(prompt, [], "أنت محامي سعودي خبير بالقانون العمالي.")
            return {"analysis": response, "legal_articles": [], "arguments": [], "conclusion": ""}
        except Exception as e:
            return {"error": str(e), "analysis": "", "legal_articles": [], "arguments": [], "conclusion": ""}

# ============ 4. توليد مستندات قانونية ============
class LegalDocumentGenerator:
    """توليد مستندات قانونية آلية (DOCX)"""
    def generate_lawsuit(self, case_data: Dict) -> bytes:
        """توليد دعوى عمالية بصيغة DOCX."""
        doc = Document()
        doc.add_heading("دعوى عمالية", level=1)
        doc.add_paragraph(f"إلى: لجنة تسوية المنازعات العمالية في {case_data.get('court_city', '...')}")
        doc.add_paragraph(f"الرقم: {case_data.get('case_number', '')}")
        doc.add_paragraph(f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}")
        doc.add_heading("بيانات المدعي:", level=2)
        doc.add_paragraph(f"الاسم: {case_data.get('plaintiff_name', '')}")
        doc.add_paragraph(f"الجنسية: {case_data.get('plaintiff_nationality', '')}")
        doc.add_paragraph(f"رقم الهوية: {case_data.get('plaintiff_id', '')}")
        doc.add_heading("بيانات المدعى عليه:", level=2)
        doc.add_paragraph(f"الاسم: {case_data.get('defendant_name', '')}")
        doc.add_paragraph(f"العنوان: {case_data.get('defendant_address', '')}")
        doc.add_heading("موضوع الدعوى:", level=2)
        doc.add_paragraph(case_data.get('case_subject', ''))
        doc.add_heading("وقائع الدعوى:", level=2)
        for i, fact in enumerate(case_data.get('facts', []), 1):
            doc.add_paragraph(f"{i}. {fact}")
        doc.add_heading("المطالبات:", level=2)
        for i, claim in enumerate(case_data.get('claims', []), 1):
            doc.add_paragraph(f"{i}. {claim}")
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

# ============ 5. حاسبة استحقاقات ============
class LegalEntitlementsCalculator:
    """حاسبة متقدمة لاستحقاقات القانون العمالي"""
    def calculate_eosb(self, basic_salary: float, total_salary: float, years_of_service: float,
                     is_arbitrary: bool = True, delay_months: int = 0, is_saudi: bool = True) -> Dict:
        """حساب مكافأة نهاية الخدمة وفقاً للمادة 84."""
        y5 = min(years_of_service, 5)
        y_plus = max(0, years_of_service - 5)
        eosb = (basic_salary / 2) * y5 + basic_salary * y_plus
        arb = (total_salary * min(12, max(3, int(years_of_service)))) if is_arbitrary else 0
        delay = total_salary * 0.05 * delay_months if delay_months > 0 else 0
        grand = eosb + arb + delay
        if not is_saudi and years_of_service < 10:
            eosb = (basic_salary / 2) * min(years_of_service, 5)
            grand = eosb + arb + delay
        return {
            "basic_salary": round(basic_salary, 2),
            "total_salary": round(total_salary, 2),
            "years_of_service": round(years_of_service, 2),
            "is_saudi": is_saudi,
            "totals": {
                "eosb_total": round(eosb, 2),
                "arbitrary_total": round(arb, 2),
                "delay_total": round(delay, 2),
                "grand_total": round(grand, 2)
            },
            "summary": [
                f"مكافأة نهاية الخدمة: {round(eosb, 2):,.2f} ريال",
                f"تعويض الفصل التعسفي: {round(arb, 2):,.2f} ريال" if is_arbitrary else None,
                f"تعويض تأخير الراتب: {round(delay, 2):,.2f} ريال" if delay_months > 0 else None,
                f"**المجموع: {round(grand, 2):,.2f} ريال**"
            ]
        }

# ============ 6. نظام تتبع المواعيد ============
class LegalDeadlinesTracker:
    """نظام تتبع المواعيد القانونية الهامة"""
    def __init__(self):
        self.deadlines = {
            "نهاية الخدمة": {"description": "مهلة رفع دعوى نهاية الخدمة", "days": 365, "article": "140", "action": "رفع دعوى إلى لجنة تسوية المنازعات العمالية"},
            "فصل تعسفي": {"description": "مهلة رفع دعوى ضد الفصل التعسفي", "days": 365, "article": "77", "action": "رفع دعوى إلى لجنة تسوية المنازعات العمالية"},
            "تأخير راتب": {"description": "مهلة امتناع العامل عن العمل بسبب تأخير الراتب", "days": 7, "article": "90", "action": "امتناع عن العمل حتى تسوية الراتب"},
            "إشعار بالإنتهاء": {"description": "مهلة إشعار صاحب العمل قبل إنهاء العقد", "days": 60, "article": "78", "action": "إشعار كتابي قبل 60 يوم"},
            "إصابة عمل": {"description": "مهلة إبلاغ عن إصابة عمل", "days": 7, "article": "131", "action": "إبلاغ صاحب العمل ووزارة العمل"},
        }

    def check_deadline(self, case_type: str, case_date: str) -> Dict:
        """التحقق من الموعد القانوني لقضية معينة."""
        if case_type not in self.deadlines:
            return {"error": "نوع قضية غير معروف"}
        deadline_info = self.deadlines[case_type]
        case_date_obj = datetime.strptime(case_date, "%Y-%m-%d")
        due_date = case_date_obj + timedelta(days=deadline_info["days"])
        today = datetime.now()
        days_remaining = (due_date - today).days
        if days_remaining < 0:
            status, color, message = "manquée", "#ff5a5a", f"انتهت المهلة منذ {-days_remaining} يوم"
        elif days_remaining <= 7:
            status, color, message = "urgente", "#ffb400", f"مهلة قصيرة - {days_remaining} يوم متبقي"
        elif days_remaining <= 30:
            status, color, message = "proche", "#ffb400", f"{days_remaining} يوم متبقي"
        else:
            status, color, message = "OK", "#4ade80", f"{days_remaining} يوم متبقي"
        return {
            "case_type": case_type,
            "description": deadline_info["description"],
            "article": deadline_info["article"],
            "case_date": case_date,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "days_remaining": days_remaining,
            "status": status,
            "color": color,
            "message": message,
            "action": deadline_info["action"]
        }

# ============ 7. نظام كشف الزلات ============
class LegalSlipDetector:
    """نظام كشف الزلات القانونية في المراسلات"""
    def __init__(self):
        self.patterns = [
            (r"(أكرهنا|أجبرنا|إكراه|ضغط|تهديد)", "إكراه على الاستقالة", "danger", "مادة 77"),
            (r"(لَا|لَمْ|مَا)\s+(نَعْتَرِف|نعرف|نقر)", "رفض الاعتراف بحقوق العامل", "danger", "مادة 84"),
            (r"(بدون|دون)\s+(تحقيق|تحقي)", "فصل بدون تحقيق", "danger", "مادة 77"),
            (r"(خطأ|خطئا)\s+(من|في)\s+(الجهة|صاحب العمل)", "إقرار بخطأ من صاحب العمل", "danger", "مادة 77"),
            (r"(حرمان|محروم)\s+(من|عن)\s+(الأجر|راتب)", "حرمان من مستحقات", "danger", "مادة 90"),
            (r"(لَا|لَمْ)\s+(يَسْتَحِق|يستحق)", "رفض استحقاق قانوني", "warn", "مادة 84"),
            (r"(تأخير)\s+(في|ب)\s+(دفع)\s+(الراتب)", "تأخير في دفع الأجر", "warn", "مادة 90"),
        ]

    def detect(self, text: str) -> List[Dict]:
        """كشف الزلات في النص."""
        findings = []
        for pattern, msg, level, article in self.patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                snippet = matches[0] if isinstance(matches[0], str) else " ".join(matches[0])
                findings.append({
                    "message": msg,
                    "level": level,
                    "snippet": snippet[:100].strip(),
                    "article": article
                })
        return findings

# ============ 8. نظام تحليل قوة القضية ============
class CaseStrengthAnalyzer:
    """نظام تحليل قوة القضية القانونية"""
    def quick_analyze(self, case_type: str, evidence_strength: str, legal_support: str) -> Dict:
        """تحليل سريع بدون AI"""
        type_scores = {"نهاية الخدمة": 8, "فصل تعسفي": 9, "تأخير راتب": 7, "إصابة عمل": 8, "منازعة عمالية": 6}
        evidence_scores = {"قوية": 3, "متوسطة": 2, "ضعيفة": 1}
        legal_scores = {"قوية": 3, "متوسطة": 2, "ضعيفة": 1}
        score = (type_scores.get(case_type, 5) * 2 +
                evidence_scores.get(evidence_strength, 2) * 3 +
                legal_scores.get(legal_support, 2) * 2) / 7
        score = min(10, max(1, round(score)))
        if score >= 8:
            strength = "قوية جداً"
        elif score >= 6:
            strength = "قوية"
        elif score >= 4:
            strength = "متوسطة"
        else:
            strength = "ضعيفة"
        return {
            "score": score,
            "strength": strength,
            "success_probability": f"{int(score * 10)}%"
        }

# ============ 9. استخراج معلومات ============
class LegalInfoExtractor:
    """استخراج معلومات قانونية سريعة من النصوص"""
    def extract_dates(self, text: str) -> List[str]:
        """استخراج التواريخ من النص"""
        patterns = [r'\d{1,2}/\d{1,2}/\d{2,4}', r'\d{4}-\d{2}-\d{2}', r'\d{1,2}-\d{1,2}-\d{2,4}']
        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        return list(set(dates))[:10]

    def extract_amounts(self, text: str) -> List[str]:
        """استخراج المبالغ المالية من النص"""
        patterns = [r'\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:ريال|SR|ر\.س|\$)', r'\d{1,3}(?:,\d{3})+(?:\.\d+)?']
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            amounts.extend(matches)
        return list(set(amounts))[:10]

    def extract_all(self, text: str) -> Dict:
        """استخراج جميع المعلومات مرة واحدة"""
        return {
            "dates": self.extract_dates(text),
            "amounts": self.extract_amounts(text),
            "articles": self.extract_articles(text),
            "names": self.extract_names(text)
        }

    def extract_articles(self, text: str) -> List[str]:
        """استخراج مواد القانون من النص"""
        patterns = [r'المادة\s+\d+', r'م\s*\d+', r'article\s+\d+']
        articles = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            articles.extend(matches)
        return list(set(articles))[:10]

    def extract_names(self, text: str) -> List[str]:
        """استخراج أسماء من النص"""
        return []

# إنشاء مثيلات عالمية
legal_classifier = LegalCaseClassifier()
legal_search = LegalSearchEngine()
rebuttal_generator = LegalRebuttalGenerator()
document_generator = LegalDocumentGenerator()
entitlements_calculator = LegalEntitlementsCalculator()
deadlines_tracker = LegalDeadlinesTracker()
slip_detector = LegalSlipDetector()
case_analyzer = CaseStrengthAnalyzer()
info_extractor = LegalInfoExtractor()