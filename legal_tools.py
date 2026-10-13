# legal_tools.py
"""
الأدوات القانونية الموحّدة — المرحلة صفر من إعادة الهيكلة.

هذه الوحدة تحل محل legal_tools_advanced.py وlitigation_tools.py معًا،
وتُنهي التضارب الذي كان قائمًا بين ثلاث فلسفات مختلفة في نفس التطبيق.

ما تم نقله كما هو (منطق سليم، لا مشكلة فيه):
- تصنيف القضايا (LegalCaseClassifier)
- استخراج التواريخ/المبالغ/المواد من النص (LegalInfoExtractor)
- محرك البحث النصي (LegalSearchEngine) — لا يزال بحثًا بعدّ الكلمات، سيُستبدل
  بمحرك دلالي حقيقي بالتضمينات في المرحلة القادمة؛ الواجهة (search) لن تتغيّر
  حتى لا ينكسر أي كود يعتمد عليها.
- مولّد نص لائحة الدعوى (LawsuitDraftGenerator) — تنسيق نص، لا حسابات مالية.
- مرجع مراحل التقاضي (LitigationTimelineReference) — معلومات عامة عن
  إجراءات المحكمة العمالية، ليست تنبؤًا بمدة قضية بعينها.
- محلّل قوة الأدلة (EvidenceStrengthScorer) — تصنيف نوعي لقوة أنواع الأدلة،
  مؤشر تنظيمي لا تنبؤ بنتيجة القضية.

ما تم إصلاحه (كان به خطأ فعلي قبل الدمج):
- تعويض الفصل التعسفي كان يُحسب بصيغة `الأجر الإجمالي × عدد أشهر (3-12)`
  ويُعرض تحت مسمى "المادة 77" رغم أن نص المادة 77 يقول صراحة:
  "تعويض لا يقل عن أجر خمسة عشر يوماً عن كل سنة من سنوات الخدمة" — أي نصف
  شهر لكل سنة، بلا حد أقصى. تم التحقق رقميًا (انظر نتائج الاختبار في تقرير
  التسليم) أن الصيغة القديمة كانت تنحرف عن الحد الأدنى النظامي بمقدار 2×
  لمعظم مدد الخدمة (3-12 سنة)، وتصل إلى 6× لخدمة أقل من 3 سنوات — والأخطر
  أنها تنعكس فوق 24 سنة خدمة فتعرض رقمًا **أقل** من الحد الأدنى النظامي
  (0.8× عند 30 سنة خدمة)، أي كانت تُظهر لموظف طويل الخدمة مبلغًا دون حقه
  القانوني الأدنى. تم استبدالها بحساب الحد الأدنى النظامي الفعلي، مع توضيح
  صريح أن الأحكام القضائية الفعلية قد تزيد عن هذا الحد حسب ظروف كل قضية.

ما تم حذفه نهائيًا من هذه الوحدة (كان "صوريًا" بلا سند نظامي):
- "تعويض تأخير الأجر = 5% × عدد أشهر التأخير" — لا يوجد نص في المادة 90
  (ولا في أي مادة أخرى في قاعدة المعرفة الحالية) يقرر نسبة مئوية كهذه؛
  المادة 90 تمنح العامل حق الامتناع عن العمل بعد 7 أيام تأخير مع بقاء
  حقوقه، وهذا ما تعرضه `wage_delay_rights` أدناه بدل رقم مالي مخترع.
- حاسبة نطاق التسوية وتكلفة التقاضي المتوقعة (SettlementCalculator) —
  نسب مئوية وصيغة أتعاب محاماة (max(5000, 10%×المطالبة)) بلا أي مصدر
  نظامي أو بيانات سوق فعلية.
- "درجة قوة القضية" واحتمال النجاح كنسبة مئوية (CaseStrengthAnalyzer) —
  رقم مخترع بالكامل من كلمات مفتاحية، أخطر أنواع المخرجات الصورية لأنه
  يوحي بدقة تنبؤية غير موجودة.
- مولّد التفنيد القانوني وتوليد DOCX ومتتبع المواعيد وكاشف "الزلات" —
  ليست معطوبة، لكنها تحتاج تصميمًا وربطًا أعمق (مواعيد workspace_store،
  قوالب DOCX حقيقية) بدل نقل سريع؛ ستُبنى في مرحلة لاحقة عن قصد لا إهمال.

كل رقم مالي في هذه الوحدة الآن يحمل نص المادة الذي استُخرج منه في مفتاح
"legal_basis"، بحيث يمكن التحقق من كل رقم مقابل مصدره مباشرة دون البحث
في مكان آخر.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from legal_database import get_legal_database
from policies import policies

_DB = get_legal_database()


def _article_text(number: str) -> str:
    art = _DB.get_article(number)
    return art["text"] if art else "نص المادة غير متوفر في قاعدة المعرفة الحالية — يلزم التحقق من المصدر الرسمي."


# ============================================================
# 1. تصنيف القضايا
# ============================================================
class LegalCaseClassifier:
    """تصنيف آلي لقضايا القانون العمالي باستخدام كلمات رئيسية."""

    CATEGORIES = {
        "نهاية الخدمة": ["نهاية خدمة", "مكافأة نهاية خدمة", "مادة 84", "علاوة نهاية"],
        "فصل تعسفي": ["فصل تعسفي", "فصل بدون سبب", "إنهاء تعسفي", "مادة 77"],
        "الأجور والرواتب": ["راتب", "أجر", "زيادة", "خصم", "مستحقات", "مادة 90", "تأخير راتب"],
        "عقد العمل": ["عقد", "عقد عمل", "تجديد", "مدة", "مادة 78", "إشعار"],
        "ساعات العمل": ["ساعات", "عمل إضافي", "فترة راحة", "مادة 98", "مادة 106"],
        "التأمينات الاجتماعية": ["تأمينات", "GOSI", "معاش", "مادة 130"],
        "المنازعات العمالية": ["منازعة", "دعوى", "محكمة", "مادة 209"],
        "السلامة المهنية": ["سلامة", "مخاطر", "حماية", "مادة 121"],
        "الإجازات": ["إجازة", "إجازة سنوية", "مادة 109", "مادة 113"],
        "التأديب": ["تأديب", "إنذار", "عقوبة", "مادة 155"],
        "إصابات العمل": ["إصابة عمل", "حادث عمل", "مادة 131"],
        "السعودة": ["سعودة", "نطاقات", "توطين"],
    }

    def classify(self, text: str) -> Tuple[str, float, List[str]]:
        text_lower = text.lower()
        scores: Dict[str, float] = {}
        matched: Dict[str, List[str]] = {}
        for category, keywords in self.CATEGORIES.items():
            found = [kw for kw in keywords if kw.lower() in text_lower]
            if found:
                scores[category] = len(found) / len(keywords)
                matched[category] = found
        if not scores:
            return "عام", 0.0, []
        best = max(scores.items(), key=lambda x: x[1])
        return best[0], round(best[1], 2), matched.get(best[0], [])

    def classify_with_ai(self, text: str, call_ai_fn: Callable) -> str:
        categories_str = "، ".join(self.CATEGORIES.keys())
        prompt = (
            f"صنّف النص القانوني التالي إلى إحدى هذه الفئات فقط:\n{categories_str}\n\n"
            f"النص:\n{text[:500]}\n\nأجب بكلمة واحدة فقط: اسم الفئة."
        )
        try:
            result = call_ai_fn(prompt, [], "أنت خبير في تصنيف القضايا القانونية السعودية.").strip()
            for cat in self.CATEGORIES:
                if cat in result:
                    return cat
            return "عام"
        except Exception:
            return "عام"


# ============================================================
# 2. محرك البحث (سيُستبدل ببحث دلالي في المرحلة القادمة)
# ============================================================
class LegalSearchEngine:
    """
    بحث قانوني حقيقي — المرحلة 1: كان عدّ تكرار كلمات حرفيًا، أصبح الآن
    مرتبطًا بـ semantic_search.py (TF-IDF فعّال الآن محليًا، مع مسار ترقية
    تلقائي للتضمينات الحقيقية إن توفرت شبكة في بيئة النشر). الواجهة (search)
    لم تتغيّر عمدًا كي لا ينكسر أي كود آخر يستدعيها.
    """

    def __init__(self):
        self.db = get_legal_database()

    def search(self, query: str, category: Optional[str] = None, max_results: int = 10) -> List[Dict]:
        from semantic_search import get_search_index
        return get_search_index().search(query, category=category, max_results=max_results)

    def search_with_ai(self, query: str, call_ai_fn: Callable, max_results: int = 5) -> List[Dict]:
        local = self.search(query, max_results=max_results)
        if local:
            return local
        prompt = f"ابحث في نظام العمل السعودي عن: {query}\nأعطني المواد القانونية ذات الصلة مع نصوصها."
        try:
            response = call_ai_fn(prompt, [], "أنت خبير في القانون العمالي السعودي.")
            return [{"title": "نتيجة AI — تحتاج تحقق مقابل نص المادة الرسمي", "text": response, "article": "AI", "category": "عام", "score": 1.0}]
        except Exception:
            return []


# ============================================================
# 3. استخراج المعلومات (تواريخ / مبالغ / مواد) من أي نص
# ============================================================
class LegalInfoExtractor:
    """استخراج معلومات قانونية من النصوص — يغذّي محرك مطابقة المستندات (matter_intelligence.cross_reference_documents)."""

    @staticmethod
    def _extract_nonoverlapping(text: str, pattern: str, flags: int = 0) -> List[str]:
        """
        ← إصلاح (المرحلة 2): الإصدار القديم كان يُشغّل عدة أنماط منفصلة
        بـ re.findall لكل منها ثم يجمع النتائج، فينتج مطابقتان لنفس القيمة
        بصيغتين مختلفتين عند تداخل الأنماط (تحقق فعلي: '18,500 ريال' مع
        '18,500' كمبلغين "مختلفين"، و'2026-02-15' مع مقطعه الفرعي
        '26-02-15' كتاريخين "مختلفين"). المسح الآن بنمط واحد مُركَّب في مرور
        واحد، والبدائل الأطول/الأدق مكتوبة أولًا كي يُفضّلها محرك regex عند
        نفس الموضع، فلا تتكرر نفس القيمة بصيغتين.
        """
        seen, out = set(), []
        for m in re.finditer(pattern, text, flags):
            val = m.group(0).strip()
            if val not in seen:
                seen.add(val)
                out.append(val)
        return out[:10]

    def extract_dates(self, text: str) -> List[str]:
        # الأطول/الأدق أولًا: YYYY-MM-DD قبل D-M-YY كي لا يُلتقط مقطع فرعي من التاريخ الكامل كتاريخ منفصل.
        pattern = r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}"
        return self._extract_nonoverlapping(text, pattern)

    def extract_amounts(self, text: str) -> List[str]:
        # المبلغ مع العملة أولًا كي لا يُلتقط الرقم المجرد داخله كمبلغ "منفصل" ثانٍ.
        pattern = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:ريال|SR|ر\.س)|\d{1,3}(?:,\d{3})+(?:\.\d+)?"
        return self._extract_nonoverlapping(text, pattern)

    def extract_articles(self, text: str) -> List[str]:
        # "المادة" الكاملة أولًا كي لا تُلتقط "مادة" (الجزء الأخير منها) كمطابقة ثانية لنفس الموضع.
        pattern = r"المادة\s+\d+|مادة\s+\d+|م\s*/\s*\d+"
        return self._extract_nonoverlapping(text, pattern, re.IGNORECASE)

    def extract_all(self, text: str) -> Dict:
        return {"dates": self.extract_dates(text), "amounts": self.extract_amounts(text), "articles": self.extract_articles(text)}


# ============================================================
# 4. حاسبة الاستحقاقات — مُعاد بناؤها بالكامل، كل رقم مُسنَد لمادته
# ============================================================
class LaborEntitlementCalculator:
    """
    حاسبة استحقاقات نظام العمل السعودي.
    قاعدة صارمة: أي رقم لا يمكن إسناده مباشرة لنص مادة صريحة لا يُحسب هنا،
    بل يُعرض كحق إجرائي أو يُترك لتقدير القضاء صراحةً.
    """

    def severance_pay(self, basic_salary: float, years_of_service: float, resignation: bool = False) -> Dict:
        """مكافأة نهاية الخدمة وفقًا للمادة 84 — الصيغة الأساسية صحيحة أصلًا ولم تتغيّر."""
        y5 = min(years_of_service, 5)
        y_plus = max(0.0, years_of_service - 5)
        full = (basic_salary / 2) * y5 + basic_salary * y_plus

        if not resignation:
            amount, note = full, "المكافأة كاملة (فصل أو انتهاء عقد لسبب غير الاستقالة)"
        elif years_of_service < 2:
            amount, note = 0.0, "لا تستحق مكافأة (استقالة قبل إتمام سنتين)"
        elif years_of_service < 5:
            amount, note = full / 3, "ثلث المكافأة (استقالة بعد 2 وقبل 5 سنوات)"
        elif years_of_service < 10:
            amount, note = full / 2, "نصف المكافأة (استقالة بعد 5 وقبل 10 سنوات)"
        else:
            amount, note = full, "المكافأة كاملة (استقالة بعد 10 سنوات فأكثر)"

        return {
            "amount": round(amount, 2),
            "note": note,
            "basic_salary": round(basic_salary, 2),
            "years_of_service": round(years_of_service, 2),
            "legal_basis": {"article": "84", "text": _article_text("84")},
            "requires_review": True,
        }

    def arbitrary_dismissal_floor(self, total_salary: float, years_of_service: float) -> Dict:
        """
        الحد الأدنى النظامي لتعويض الفصل التعسفي وفق نص المادة 77 حرفيًا:
        أجر خمسة عشر يومًا عن كل سنة خدمة = نصف الأجر الإجمالي الشهري × سنوات الخدمة.
        هذا حد أدنى فقط، لا رقم نهائي — للمحكمة سلطة تقديرية بالزيادة عنه.
        """
        daily_wage = total_salary / 30
        floor_amount = daily_wage * 15 * years_of_service
        return {
            # "amount" مضافة (مع إبقاء "statutory_floor" نفسها) للاتساق مع
            # كل دوال الحاسبة الأخرى التي تُعيد "amount" — غيابها هنا تحديدًا
            # كان يُسقط هذا الرقم بالذات صامتًا من أي تجميع عام يبحث عن "amount".
            "amount": round(floor_amount, 2),
            "statutory_floor": round(floor_amount, 2),
            "calculation": f"({total_salary:,.0f} ÷ 30 يوم) × 15 يوم × {years_of_service:.2f} سنة",
            "total_salary": round(total_salary, 2),
            "years_of_service": round(years_of_service, 2),
            "legal_basis": {"article": "77", "text": _article_text("77")},
            "caveat": "هذا هو الحد الأدنى النظامي المنصوص عليه حرفيًا فقط. الأحكام القضائية الفعلية قد تزيد عنه بحسب ظروف كل قضية وسلطة القاضي التقديرية — راجع سوابق قضائية مشابهة أو استشر محاميًا لتقدير واقعي.",
            "requires_review": True,
        }

    def wage_delay_rights(self, days_delayed: int) -> Dict:
        """
        لا نسبة مالية جاهزة هنا عمدًا — المادة 90 لا تقرر نسبة تعويض عن
        التأخير، بل تمنح حقًا إجرائيًا فقط.
        """
        eligible = days_delayed > 7
        return {
            "days_delayed": days_delayed,
            "right_to_refuse_work": eligible,
            "explanation": (
                "تجاوز التأخير 7 أيام: يحق للعامل الامتناع عن العمل مع بقاء كامل حقوقه، وفق نص المادة 90 حرفيًا."
                if eligible
                else "التأخير 7 أيام أو أقل: لم يتجاوز بعد المهلة التي تمنح حق الامتناع عن العمل وفق نص المادة 90."
            ),
            "legal_basis": {"article": "90", "text": _article_text("90")},
            "note": "لا يوجد نص في هذه المادة يحدد نسبة تعويض مالي عن مدة التأخير نفسها؛ أي مطالبة مالية إضافية عن ضرر التأخير تحتاج إسنادًا وإثباتًا منفصلين، لا صيغة تلقائية.",
        }

    def overtime_pay(self, hourly_rate: float, overtime_hours: float) -> Dict:
        """أجر العمل الإضافي وفق المادة 106 — 150% من الأجر العادي، صحيحة أصلًا."""
        pay = hourly_rate * overtime_hours * 1.5
        return {
            "amount": round(pay, 2),
            "hourly_rate": round(hourly_rate, 2),
            "overtime_hours": overtime_hours,
            "rate_applied": "150% من أجر الساعة العادية",
            "legal_basis": {"article": "106", "text": _article_text("106")},
        }

    def annual_leave_balance(self, start_date: str, end_date: str = "") -> Dict:
        """رصيد الإجازة السنوية وفق المادة 109."""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
            years = (end - start).days / 365.25
            annual_days = 30 if years >= 5 else 21
            return {
                "start_date": start_date,
                "end_date": end_date or end.strftime("%Y-%m-%d"),
                "total_years": round(years, 2),
                "annual_days_rate": annual_days,
                "earned_days": round(years * annual_days, 1),
                "legal_basis": {"article": "109", "text": _article_text("109")},
                "note": "الحساب تناسبي بسيط؛ لا يحتسب انقطاعات الإجازات المستخدمة فعليًا — قارنه بسجلات صاحب العمل.",
            }
        except Exception as e:
            return {"error": str(e), "legal_basis": {"article": "109", "text": _article_text("109")}}


# ============================================================
# 5. تحليل قوة الأدلة — مؤشر تنظيمي، ليس تنبؤًا بنتيجة القضية
# ============================================================
class EvidenceStrengthScorer:
    EVIDENCE_TYPES = {
        "مستند رسمي حكومي": {"weight": 10, "desc": "أعلى درجات الإثبات — خطاب رسمي، حكم سابق، شهادة GOSI"},
        "عقد عمل موثق": {"weight": 9, "desc": "عقد موقع من الطرفين وموثق لدى الوزارة"},
        "إشعار كتابي مثبت بالاستلام": {"weight": 8, "desc": "إشعار إنهاء، إنذار، مراسلة رسمية بشرط إثبات الاستلام"},
        "كشف راتب بنكي": {"weight": 8, "desc": "دليل قاطع على الأجر الفعلي"},
        "تقرير طبي رسمي": {"weight": 9, "desc": "في إصابات العمل — دليل قاطع"},
        "محضر تحقيق داخلي": {"weight": 7, "desc": "وثيقة تحقيق موقعة من أطراف متعددة"},
        "بريد إلكتروني رسمي": {"weight": 6, "desc": "بريد عمل رسمي مع إيصال قراءة"},
        "شهادة شاهدين": {"weight": 6, "desc": "شاهدان يعززان بعضهما"},
        "تسجيل صوتي": {"weight": 5, "desc": "قد يُقبل إذا لم يكن فيه انتهاك للخصوصية"},
        "رسالة واتساب/نصية": {"weight": 4, "desc": "قد تُقبل كقرينة إذا كانت واضحة وغير منقطعة"},
        "صورة/لقطة شاشة": {"weight": 3, "desc": "تُقبل كقرينة معززة فقط"},
        "شهادة شاهد واحد": {"weight": 3, "desc": "شهادة الشهود مقبولة مع قرائن أخرى"},
    }

    REQUIRED_BY_CASE_TYPE = {
        "فصل تعسفي": ["إشعار كتابي مثبت بالاستلام", "كشف راتب بنكي", "عقد عمل موثق"],
        "نهاية الخدمة": ["عقد عمل موثق", "كشف راتب بنكي", "مستند رسمي حكومي"],
        "تأخير راتب": ["كشف راتب بنكي", "عقد عمل موثق"],
        "إصابة عمل": ["تقرير طبي رسمي", "مستند رسمي حكومي", "شهادة شاهدين"],
    }

    def score(self, evidence_list: List[Dict]) -> Dict:
        total, details, types_found = 0, [], set()
        for ev in evidence_list:
            info = self.EVIDENCE_TYPES.get(ev.get("type", ""))
            if not info:
                continue
            total += info["weight"]
            types_found.add(ev["type"])
            details.append({"type": ev["type"], "weight": info["weight"], "note": info["desc"], "date": ev.get("date", "")})
        coverage_index = min(100, round((total / (len(evidence_list) * 10)) * 100)) if evidence_list else 0
        return {
            "coverage_index": coverage_index,
            "evidence_count": len(evidence_list),
            "details": details,
            "disclaimer": "مؤشر تنظيمي لجودة مجموعة الأدلة المتاحة مقارنة بأعلى تصنيف ممكن — وليس تنبؤًا بنتيجة القضية أو احتمال كسبها.",
        }

    def gaps_for(self, case_type: str) -> List[str]:
        return self.REQUIRED_BY_CASE_TYPE.get(case_type, [])


# ============================================================
# 6. مولّد نص لائحة الدعوى — تنسيق، لا حسابات
# ============================================================
class LawsuitDraftGenerator:
    def draft(self, case_data: Dict) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        facts = case_data.get("facts", [])
        claims = case_data.get("claims", [])
        evidence = case_data.get("evidence", [])
        articles = case_data.get("articles", [])
        facts_text = "\n".join(f"{i}. {f}" for i, f in enumerate(facts, 1)) or "—"
        claims_text = "\n".join(f"{i}. {c}" for i, c in enumerate(claims, 1)) or "—"
        evidence_text = "\n".join(f"{i}. {e}" for i, e in enumerate(evidence, 1)) or "—"
        articles_text = "، ".join(f"المادة ({a}) من نظام العمل" for a in articles) or "نظام العمل السعودي"
        return f"""بسم الله الرحمن الرحيم

                        لائحة دعوى عمالية — مسودة للمراجعة قبل التقديم

إلى معالي رئيس المحكمة العمالية الموقر                                  التاريخ: {today}

أولاً: بيانات المدعي
- الاسم: {case_data.get('plaintiff_name', '____________')}
- رقم الهوية: {case_data.get('plaintiff_id', '____________')}

ثانياً: بيانات المدعى عليه
- الاسم: {case_data.get('defendant_name', '____________')}

ثالثاً: الوقائع
{facts_text}

رابعاً: المطالبات
{claims_text}

خامساً: الإسناد القانوني
تستند هذه الدعوى إلى {articles_text} ولائحته التنفيذية.

سادساً: الأدلة المرفقة
{evidence_text}

— مسودة أولية تحتاج مراجعة محامٍ مرخّص قبل أي تقديم رسمي —
"""


# ============================================================
# 7. مرجع مراحل التقاضي — معلومات عامة، ليست جدولاً زمنيًا لقضية بعينها
# ============================================================
class LitigationTimelineReference:
    STAGES = [
        {"stage": 1, "name": "التسوية الودية", "duration_text": "حتى 21 يوم عمل من أول جلسة", "note": "مرحلة إلزامية أولى قبل رفع الدعوى"},
        {"stage": 2, "name": "محضر تعذر التسوية", "duration_text": "عند فشل التسوية", "note": "يُصدر عند عدم الاتفاق، ويُشترط لرفع الدعوى"},
        {"stage": 3, "name": "رفع لائحة الدعوى عبر ناجز", "duration_text": "متغيّر", "note": "تحديد موعد أول جلسة عادة خلال 30-60 يوم"},
        {"stage": 4, "name": "الجلسة الأولى وتبادل المذكرات", "duration_text": "حتى 30 يوم", "note": ""},
        {"stage": 5, "name": "جلسات الإثبات والمرافعة", "duration_text": "30-90 يوم", "note": ""},
        {"stage": 6, "name": "الحكم الابتدائي", "duration_text": "حتى 30 يوم", "note": "30 يومًا لأي طرف للاستئناف"},
        {"stage": 7, "name": "الاستئناف (اختياري)", "duration_text": "60-120 يوم", "note": ""},
        {"stage": 8, "name": "تنفيذ الحكم", "duration_text": "حتى 30 يوم", "note": ""},
    ]

    def timeline(self) -> Dict:
        return {
            "stages": self.STAGES,
            "important_note": "المدد تقديرية عامة من واقع الإجراءات المعلنة وتختلف فعليًا حسب ظروف كل قضية وضغط العمل في المحاكم؛ ليست وعدًا بمدة محددة.",
        }


# ============================================================
# 8. محرك المواعيد والتقادم — المرحلة 3
# ============================================================
def _add_years_safe(d: datetime, years: int) -> datetime:
    """إضافة سنوات مع معالجة 29 فبراير بأمان (يرتد إلى 28 فبراير إن لم توجد السنة الكبيسة المقابلة)."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)


class DeadlineEngine:
    """
    أخطر عنصر منفرد في أي نزاع عمل: فوات الموعد قد يُسقط الحق كاملًا بصرف
    النظر عن قوة القضية نفسها. كل موعد هنا مُسنَد لنص مادة صريح موجود في
    قاعدة المعرفة؛ لا تقدير اجتهادي لمدة غير منصوص عليها فيها.
    """

    def prescription_deadline(self, reference_date: str, claim_type: str = "عقد") -> Dict:
        """المادة 222: تقادم دعاوى عقد العمل بسنة من انتهاء العقد؛ دعاوى إصابات العمل بثلاث سنوات من الإصابة."""
        try:
            ref = datetime.strptime(reference_date, "%Y-%m-%d")
        except Exception as e:
            return {"error": f"صيغة التاريخ يجب أن تكون YYYY-MM-DD: {e}"}

        years = 3 if claim_type == "إصابة عمل" else 1
        deadline = _add_years_safe(ref, years)
        days_left = (deadline - datetime.now()).days
        if days_left < 0:
            status = "منقضٍ ظاهريًا — لا تفترض سقوط الحق تلقائيًا؛ قد يكون التقادم قد تَوقّف أو انقطع بسبب نظامي (كمطالبة رسمية سابقة)، راجع محاميًا فورًا"
        elif days_left < 60:
            status = "عاجل جدًا"
        elif days_left < 180:
            status = "يحتاج متابعة قريبة"
        else:
            status = "ضمن المدة حاليًا"
        return {
            "reference_date": reference_date,
            "claim_type": claim_type,
            "prescription_years": years,
            "deadline": deadline.strftime("%Y-%m-%d"),
            "days_remaining": days_left,
            "status": status,
            "legal_basis": {"article": "222", "text": _article_text("222")},
            "caveat": "حساب مباشر من تاريخ مرجعي واحد فقط. أسباب وقف/انقطاع التقادم النظامية غير مُدخلة هنا — لا تعتمد على هذا الرقم وحده قرب الموعد أو بعده مباشرة دون استشارة محامٍ.",
        }

    def notice_period_compliance(self, notice_given_days: int, monthly_paid: bool = True) -> Dict:
        """المادة 78: 60 يومًا للعمال المعينين بأجر شهري، 30 يومًا لغيرهم."""
        required = 60 if monthly_paid else 30
        return {
            "required_days": required,
            "notice_given_days": notice_given_days,
            "compliant": notice_given_days >= required,
            "shortfall_days": max(0, required - notice_given_days),
            "legal_basis": {"article": "78", "text": _article_text("78")},
        }

    def all_deadlines(self, termination_date: str, claim_type: str = "عقد", notice_given_days: Optional[int] = None, monthly_paid: bool = True) -> Dict:
        result = {
            "prescription": self.prescription_deadline(termination_date, claim_type),
            "amicable_settlement_note": "بعد تسجيل طلب التسوية الودية: 21 يوم عمل من تاريخ أول جلسة قبل الإحالة للمحكمة العمالية (التفاصيل الإجرائية الكاملة والمصدر الرسمي في legal_intelligence.PROCEDURE_REQUIREMENTS).",
        }
        if notice_given_days is not None:
            result["notice_compliance"] = self.notice_period_compliance(notice_given_days, monthly_paid)
        return result


# ============================================================
# 9. فحص مشروعية الإنهاء — قائمة تحقق مُسنَدة، لا نسبة نجاح مُخترعة
# ============================================================
class TerminationLegalityAssessment:
    """
    قائمة تحقق مبنية على نصوص صريحة (المواد 77، 78، 80، 81) لتحديد أي مسار
    نظامي ينطبق على الوقائع والدليل المطلوب لإثباته — لا درجة احتمال أو
    نسبة نجاح مُخترعة (بالضبط نوع المخرج "الصوري" المرفوض في هذا المشروع).
    """

    # المادة 81: حالات حصرية يجوز فيها لصاحب العمل الفصل دون إشعار
    EMPLOYER_VALID_GROUNDS = [
        {"key": "assault_on_employer", "label": "اعتداء العامل على صاحب العمل", "evidence_needed": ["محضر الواقعة", "شهادة شهود", "بلاغ رسمي إن وُجد"]},
        {"key": "unauthorized_absence", "label": "غياب غير مبرر أكثر من 30 يومًا في السنة أو 15 يومًا متواصلة", "evidence_needed": ["سجل الحضور والانصراف", "إشعارات الغياب الموجهة للعامل"]},
        {"key": "disclosure_of_secrets", "label": "إفشاء أسرار العمل", "evidence_needed": ["إثبات طبيعة المعلومة كسرّ عمل", "دليل الإفشاء الفعلي"]},
    ]

    # المادة 80: حالات حصرية يجوز فيها للعامل ترك العمل دون إشعار مع بقاء حقوقه كاملة
    WORKER_VALID_GROUNDS = [
        {"key": "employer_breach", "label": "إخلال صاحب العمل بالتزاماته التعاقدية (كعدم دفع الأجر)", "evidence_needed": ["كشوف رواتب تُظهر التأخير/عدم الدفع", "المراسلات مع صاحب العمل"]},
        {"key": "assault_or_abuse", "label": "تعرّض العامل للاعتداء أو الإساءة", "evidence_needed": ["تقرير طبي إن وُجد", "محضر رسمي", "شهادة شهود"]},
    ]

    def assess(self, initiated_by: str, notice_given_days: int = 0, monthly_paid: bool = True, employer_claimed_ground: Optional[str] = None, worker_claimed_ground: Optional[str] = None) -> Dict:
        if initiated_by not in {"صاحب العمل", "العامل"}:
            return {"error": "initiated_by يجب أن تكون 'صاحب العمل' أو 'العامل'"}

        required = 60 if monthly_paid else 30
        notice = {"required_days": required, "given_days": notice_given_days, "sufficient": notice_given_days >= required}
        findings: List[Dict] = []
        path = ""

        if initiated_by == "صاحب العمل":
            if notice["sufficient"]:
                path = "إنهاء بإشعار كافٍ (المادة 78) — لا حاجة لإثبات سبب من المادة 81، ومكافأة نهاية الخدمة (المادة 84) مستحقة بصرف النظر عن السبب."
            elif employer_claimed_ground:
                ground = next((g for g in self.EMPLOYER_VALID_GROUNDS if g["key"] == employer_claimed_ground), None)
                if ground:
                    findings.append({"type": "سبب ضمن حالات المادة 81 الحصرية", "ground": ground["label"], "note": "عبء إثبات توفر هذا السبب فعليًا يقع على صاحب العمل.", "evidence_needed": ground["evidence_needed"], "legal_basis": {"article": "81", "text": _article_text("81")}})
                    path = "فصل دون إشعار بسبب مُدَّعى من حالات المادة 81 — مشروط بإثبات صاحب العمل لتوفره فعليًا."
                else:
                    path = "السبب المذكور غير مدرج ضمن حالات المادة 81 الحصرية (وهي حصرية لا قياس عليها) — مؤشر نحو فصل تعسفي بموجب المادة 77."
                    findings.append({"type": "مؤشر فصل تعسفي", "note": "استخدم arbitrary_dismissal_floor() لحساب الحد الأدنى النظامي للتعويض.", "legal_basis": {"article": "77", "text": _article_text("77")}})
            else:
                path = "إنهاء دون إشعار كافٍ ودون سبب من حالات المادة 81 — هذا هو النمط الذي تتناوله المادة 77 (فصل تعسفي): تعويض لا يقل عن أجر 15 يومًا عن كل سنة خدمة."
                findings.append({"type": "مؤشر فصل تعسفي", "note": "استخدم arbitrary_dismissal_floor() لحساب الحد الأدنى النظامي للتعويض.", "legal_basis": {"article": "77", "text": _article_text("77")}})
        else:  # العامل
            if worker_claimed_ground:
                ground = next((g for g in self.WORKER_VALID_GROUNDS if g["key"] == worker_claimed_ground), None)
                if ground:
                    findings.append({"type": "سبب ضمن حالات المادة 80 الحصرية", "ground": ground["label"], "note": "عبء الإثبات على العامل؛ عند الإثبات تُحفظ كل حقوقه كاملة رغم عدم الإشعار.", "evidence_needed": ground["evidence_needed"], "legal_basis": {"article": "80", "text": _article_text("80")}})
                    path = "ترك عمل دون إشعار بسبب مُدَّعى من حالات المادة 80 — مشروط بالإثبات، وعند الإثبات تُحفظ كل الحقوق."
                else:
                    path = "السبب المذكور غير مدرج ضمن حالات المادة 80 الحصرية — واجب الإشعار المسبق (المادة 78) يبقى قائمًا ما لم يثبت سبب مدرج فعليًا."
            elif notice["sufficient"]:
                path = "استقالة بإشعار كافٍ (المادة 78) — الاستقالة تُخفّض نسبة مكافأة نهاية الخدمة حسب سنوات الخدمة، راجع severance_pay()."
            else:
                path = "ترك عمل دون إشعار كافٍ ودون سبب من حالات المادة 80 — قد يعرّض العامل لمطالبة صاحب العمل بتعويض عن عدم الإشعار؛ راجع محاميًا قبل اتخاذ خطوة إضافية."

        return {
            "initiated_by": initiated_by,
            "notice": notice,
            "path_assessment": path,
            "findings": findings,
            "requires_review": True,
            "disclaimer": "قائمة تحقق لتوجيه جمع الأدلة وتحديد المسار النظامي الأرجح بناءً على نصوص صريحة — وليست حكمًا قضائيًا ولا تأكيدًا لمشروعية أو عدم مشروعية أي إنهاء فعلي.",
        }


deadline_engine = DeadlineEngine()
termination_assessment = TerminationLegalityAssessment()


# ============================================================
# 10. ورقة العمل الشاملة — تجمع كل الحاسبات في تقرير منهجي واحد
# ============================================================
def full_entitlements_worksheet(basic_salary: float, total_salary: float, start_date: str, end_date: str, termination_type: str, notice_given_days: int = 0, monthly_paid: bool = True, unused_leave_days: Optional[float] = None, overtime_hours: float = 0, overtime_hourly_rate: Optional[float] = None) -> Dict:
    """
    termination_type: 'فصل تعسفي' | 'فصل بسبب (م81)' | 'استقالة' | 'انتهاء مدة العقد'.
    تجمّع كل حاسبات LaborEntitlementCalculator ومحرك المواعيد في تقرير واحد
    منهجي بدل استدعاء كل أداة منفردة يدويًا. كل بند مُسنَد لمادته صراحةً،
    وأي بند لا يمكن حسابه برقم موثوق من قاعدة المعرفة الحالية يُذكر صراحةً
    ضمن items_needing_further_info بدل حذفه بصمت أو اختلاق رقم له.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception as e:
        return {"error": f"صيغة التاريخ يجب أن تكون YYYY-MM-DD: {e}"}
    years = (end - start).days / 365.25

    items: List[Dict] = []
    resignation = termination_type == "استقالة"
    items.append({"item": "مكافأة نهاية الخدمة", **entitlement_calculator.severance_pay(basic_salary, years, resignation=resignation)})

    if termination_type == "فصل تعسفي":
        items.append({"item": "الحد الأدنى لتعويض الفصل التعسفي", **entitlement_calculator.arbitrary_dismissal_floor(total_salary, years)})

    if unused_leave_days:
        daily_wage = total_salary / 30
        items.append({
            "item": "بدل رصيد الإجازة غير المستخدمة", "amount": round(daily_wage * unused_leave_days, 2),
            "calculation": f"({total_salary:,.0f} ÷ 30) × {unused_leave_days} يوم",
            "legal_basis": {"article": "109", "text": _article_text("109")},
            "note": "بدل نقدي لرصيد الإجازة غير المستخدم عند انتهاء العلاقة — طابق الرصيد المُدخل هنا مع سجلات صاحب العمل الفعلية.",
        })

    if overtime_hours and overtime_hourly_rate:
        items.append({"item": "أجر العمل الإضافي المتراكم", **entitlement_calculator.overtime_pay(overtime_hourly_rate, overtime_hours)})

    notice_check = deadline_engine.notice_period_compliance(notice_given_days, monthly_paid)
    if not notice_check["compliant"] and termination_type != "استقالة":
        items.append({
            "item": "احتمال استحقاق تعويض عن نقص مهلة الإشعار", "amount": None,
            "legal_basis": {"article": "78", "text": _article_text("78")},
            "note": f"الإشعار المُعطى {notice_given_days} يوم أقل من المطلوب {notice_check['required_days']} يوم. نص المادة 78 المتاح هنا لا يحدد صيغة تعويض بديلة صريحة؛ لا يُحسب رقم تلقائيًا تفاديًا لاختلاقه بلا سند — هذا بند يحتاج تأكيدًا من محامٍ أو من مادة إضافية غير متوفرة في قاعدة المعرفة الحالية.",
        })

    confident_total = sum(i["amount"] for i in items if isinstance(i.get("amount"), (int, float)))
    return {
        "inputs": {"basic_salary": basic_salary, "total_salary": total_salary, "years_of_service": round(years, 2), "termination_type": termination_type},
        "items": items,
        "confident_total_sar": round(confident_total, 2),
        "items_needing_further_info": [i["item"] for i in items if i.get("amount") is None],
        "deadlines": deadline_engine.all_deadlines(end_date, "عقد", notice_given_days, monthly_paid),
        "disclaimer": "تقدير أولي مبني فقط على المواد المتوفرة في قاعدة المعرفة الحالية. لا يشمل أي بند تقديره القضاء وحده أو غير مُدرج صراحة أعلاه. يجب مراجعة محامٍ مرخّص قبل أي مطالبة أو تسوية فعلية.",
    }


# ============================================================
# 11. تنبيه التصعيد لمحامٍ — مربوط فعليًا بـ policies.py
# ============================================================
# قيمة استرشادية قابلة للتعديل من قبل المستخدم لاحقًا؛ ليست نصًا نظاميًا.
_HIGH_VALUE_CLAIM_THRESHOLD_SAR = 50_000


def check_escalation(text: str, claim_amount: Optional[float] = None) -> Dict:
    """يفحص نص القضية مقابل معايير policies.py الفعلية لتحديد ضرورة التصعيد لمحامٍ."""
    triggers = policies.risk_management_policy()["escalate_to_lawyer"]
    text_lower = (text or "").lower()
    matched = [t for t in triggers if any(w in text_lower for w in t.split())]
    amount_trigger = claim_amount is not None and claim_amount >= _HIGH_VALUE_CLAIM_THRESHOLD_SAR
    return {
        "should_escalate": bool(matched) or amount_trigger,
        "matched_triggers": matched,
        "amount_trigger": amount_trigger,
        "threshold_note": f"عتبة استرشادية داخلية ({_HIGH_VALUE_CLAIM_THRESHOLD_SAR:,} ريال) قابلة للتعديل، وليست حدًا نظاميًا.",
        "disclaimer": policies.get_disclaimer(),
    }


# ============================================================
# نسخ عالمية — نفس الأسماء التي كانت تُستورد من legal_tools_advanced
# لضمان أن أي كود آخر يستورد هذه الأسماء يستمر بالعمل دون تعديل.
# ============================================================
legal_classifier = LegalCaseClassifier()
legal_search = LegalSearchEngine()
info_extractor = LegalInfoExtractor()
entitlement_calculator = LaborEntitlementCalculator()
evidence_scorer = EvidenceStrengthScorer()
lawsuit_drafter = LawsuitDraftGenerator()
litigation_timeline = LitigationTimelineReference()
