# analysis_engine.py
"""
محرك التحليل القانوني: 18 محوراً متكاملاً لقانون العمل السعودي.
"""

from typing import List, Dict, Callable, Optional
from legal_database import get_legal_database
from legal_tools_advanced import legal_search, legal_classifier

ANALYSIS_AXES = [
    {"id": "procedural", "name": "الإجرائي", "icon": "📋",
     "system": "أنت خبير في الإجرائات القانونية لنظام العمل السعودي. ركز على: هل اتبعت الإجرائات الصحيحة؟ (تحقيق، إنذار، نهلة إشعار، توثيق). اذكر كل إخلال إجرائي ورقم المادة المرتبطة به."},
    {"id": "financial", "name": "المالي", "icon": "💰",
     "system": "أنت خبير في الجوانب المالية لنظام العمل السعودي. احسب: نهاية الخدمة (م84)، التعويضات (م77)، التأخرات (م90). اذكر الأرقام والتواريخ بدقة."},
    {"id": "evidentiary", "name": "الإثباتي", "icon": "🔍",
     "system": "أنت قاضي في محكمة العمل السعودية. قيّم: ما هو نوثق وما هو غير نوثق؟ ما هي المستندات التي تحتاج إلى إحضارها؟ كيف يمكن إثبات كل طرف؟"},
    {"id": "disciplinary", "name": "التأديبي", "icon": "⚖️",
     "system": "أنت محامي متخصص في القضايا التأديبية. حلل: هل كانت العقوبة متناسبة مع المخالفة؟ هل سبقتها التحقيقات اللازمة؟"},
    {"id": "contractual", "name": "التعاقدي", "icon": "📄",
     "system": "أنت خبير في عقود العمل. حدد: هل العقد محدد المدة أم غير محدد؟ هل تم تجديده بشكل صحيح؟"},
    {"id": "administrative", "name": "الإداري", "icon": "🏛️",
     "system": "أنت خبير في الإجرائات الإدارية لوزارة العمل. حلل: هل تم إتباع اللوائح الإدارية؟"},
    {"id": "constitutional", "name": "الدستوري", "icon": "🏛️",
     "system": "أنت خبير في المبادئ الدستورية للحقوق العمالية. حلل: هل هناك انتهاك لحقوق دستورية؟"},
    {"id": "limitation", "name": "التقادم", "icon": "⏳",
     "system": "أنت خبير في مواعيد التقادم القانونية. احسب: متى ينقضي الحق في رفع الدعوى؟"},
    {"id": "witness", "name": "الشهود", "icon": "👥",
     "system": "أنت محامي متخصص في استجواب الشهود. حلل: من يمكن استدعاؤه كشاهد؟"},
    {"id": "communications", "name": "المراسلات", "icon": "📧",
     "system": "أنت خبير في تحليل المراسلات القانونية. ابحث عن: إقارات بالزلات (م77), تأخرات في الدفع (م90)."},
    {"id": "retaliation", "name": "الانتقام", "icon": "🎯",
     "system": "أنت خبير في قضايا التعسف والانتقام. حلل: هل هناك دليل على انتقام من قبل صاحب العمل؟"},
    {"id": "performance_eval", "name": "تقييمات الأداء", "icon": "📊",
     "system": "أنت خبير في أنظمة تقييم الأداء. حلل: هل كانت التقييمات عادلة؟"},
    {"id": "leave_rights", "name": "الإجازات", "icon": "🗓️",
     "system": "أنت خبير في حقوق الإجازات. احسب: الإجازة السنوية (م53), إجازة المرض (م39)."},
    {"id": "access_suspension", "name": "تعليق العمل", "icon": "🚫",
     "system": "أنت خبير في قضايا تعليق العمل. حلل: هل التعليق قانوني؟"},
    {"id": "salary_deduction", "name": "الخصومات", "icon": "✂️",
     "system": "أنت خبير في قانون الخصومات من الأجر. حلل: هل الخصومات قانونية؟ (م91)"},
    {"id": "complaint_mechanism", "name": "آليات الشكوى", "icon": "📨",
     "system": "أنت خبير في آليات الشكوى في وزارة العمل. حدد: ما هي آليات الشكوى المتاحة؟"},
    {"id": "comparative_precedent", "name": "السوابق القضائية", "icon": "📚",
     "system": "أنت قاضي في محكمة العمل السعودية. استخلص: ما هي السوابق القضائية المشابهة؟"},
    {"id": "strategic", "name": "الاستراتيجي", "icon": "🗡️",
     "system": "أنت مستشار قانوني استراتيجي. رتب: ما هي أفضل استراتيجية لهذه القضية؟"}
]

CONSENSUS_SYSTEM = """
أنت رئيس هيئة تحليل قانوني. لديك 18 محوراً متخصصاً حللوا نفس القضية.
المهمة: جمع كل التحليلات في إجماع واحد شامل.
المتطلبات:
1. اذكر أهم 5 نقاط اتفقت عليها جميع المحاور.
2. اذكر أي تعارض بين التحليلات وكيف يمكن حله.
3. اختم بتوصية نهائية واضحة للمستخدم.
"""

def run_full_analysis(case_text: str, call_ai_fn: Callable[[str, List[Dict], str], str],
                     progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Dict:
    results = []
    total = len(ANALYSIS_AXES)
    for i, axis in enumerate(ANALYSIS_AXES, start=1):
        if progress_callback:
            progress_callback(i, total, axis["name"])
        prompt = f"حّلل القضية القانونية التالية من منظور {axis['name']} فقط:\n\n{case_text}"
        try:
            answer = call_ai_fn(prompt, [], axis["system"])
        except Exception as e:
            answer = f"⚠️ تعذر تحليل هذا المحور: {str(e)[:150]}"
        results.append({"id": axis["id"], "name": axis["name"], "icon": axis["icon"], "answer": answer})

    combined = "\n\n".join(f"### {r['icon']} {r['name']}\n{r['answer']}" for r in results)
    consensus_prompt = f"إليك خلاصات 18 محوراً:\n\n{combined}\n\nابنِ الآن الإجماع النهائي."
    try:
        consensus = call_ai_fn(consensus_prompt, [], CONSENSUS_SYSTEM)
    except Exception as e:
        consensus = f"⚠️ تعذر بناء الإجماع: {str(e)[:150]}"
    return {"axes": results, "consensus": consensus}

def search_legal_database(query: str, category: Optional[str] = None, max_results: int = 10) -> List[Dict]:
    return legal_search.search(query, category, max_results)

def classify_case(text: str, call_ai_fn: Optional[Callable] = None):
    if call_ai_fn:
        return legal_classifier.classify_with_ai(text, call_ai_fn)
    return legal_classifier.classify(text)


def get_all_categories() -> List[str]:
    """
    جلب جميع تصنيفات القانون العمالي.
    ← إصلاح: هذه الدالة كانت مفقودة وتسبب NameError
    """
    db = get_legal_database()
    return db.get_all_categories()


def search_saudi_labor_laws(query: str, max_results: int = 10) -> List[Dict]:
    """
    بحث في نصوص نظام العمل السعودي.
    ← إصلاح: هذه الدالة كانت مفقودة وتسبب NameError
    """
    return legal_search.search(query, max_results=max_results)


def search_with_ai(query: str, call_ai_fn: Callable, max_results: int = 5) -> List[Dict]:
    """
    بحث مُعزَّز بالذكاء الاصطناعي.
    ← إصلاح: هذه الدالة كانت مفقودة وتسبب NameError
    """
    return legal_search.search_with_ai(query, call_ai_fn, max_results)