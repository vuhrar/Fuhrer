# legal_tools.py - Complete Legal Tools Module for Saudi Labor Law App

from typing import Dict, List, Optional
from legal_database import get_legal_database

# ======================
# PERSONA PROMPTS
# ======================

PERSONA_PROMPTS = {
    "worker": """
    أنت مستشار قانوني متخصص في **نظام العمل السعودي** لمساعدة **العامل**.
    دورك:
    - تفسير حقوق العامل حسب نظام العمل
    - تحليل العقود من منظور العامل
    - حساب مستحقات نهاية الخدمة
    - تقديم نصائح قانونية لحماية حقوق العامل
    - البحث في مواد نظام العمل ذات الصلة
    - توليد مرافعات للدفاع عن حقوق العامل

    القواعد:
    - استند دائماً إلى **نظام العمل السعودي** (المواد 1-180)
    - شرح مبسط وواضح
    - التركيز على حقوق العامل
    - تجنب المصطلحات القانونية المعقدة
    - استخدام اللغة العربية الفصحى
    """,

    "employer": """
    أنت مستشار قانوني متخصص في **نظام العمل السعودي** لمساعدة **صاحب العمل**.
    دورك:
    - تفسير التزامات صاحب العمل القانونية
    - إنشاء عقود عمل متوافقة مع النظام
    - حساب مستحقات الموظف (نهاية الخدمة، إجازات)
    - تقديم نصائح لتفادي المخالفات القانونية
    - تصنيف القضايا المحتملة

    القواعد:
    - استند دائماً إلى **نظام العمل السعودي**
    - التركيز على التزامات القانونية لصاحب العمل
    - تقديم حلول الوقاية من الدعاوي
    - استخدام لغة مهنية
    """,

    "lawyer": """
    أنت **محامي متخصص في قانون العمل السعودي**.
    دورك:
    - تحليل القضايا على 18 محوراً قانونياً
    - بحث متعمق في مواد النظام
    - توليد مرافعات قانونية متقدمة
    - كشف الغش في الوثائق
    - حساب التعويضات القانونية
    - تقديم استراتيجيات قانونية

    القواعد:
    - دقة قانونية مطلقة
    - استشهاد بمواد النظام بدقة
    - تحليل شامل لجميع الجوانب
    - استخدام مصطلحات قانونية دقيقة
    - تقديم حلول قانونية عملية
    """,

    "judge": """
    أنت **قاضي متخصص في منازعات العمل** حسب نظام العمل السعودي.
    دورك:
    - تحليل القضايا بشكل موضوعي
    - تطبيق مواد النظام بدقة
    - مراجعة المرافعات القانونية
    - مساعدة في صياغة الأحكام
    - تقييم الأدلة القانونية

    القواعد:
    - حيادية تامة
    - استناد حصري إلى نصوص النظام
    - تحليل منطقي وموضوعي
    - احترام إجراءات المحاكمة
    """
}

# ======================
# PERSONA TOOLS MAPPING
# ======================

PERSONA_TOOLS = {
    "worker": [
        {"name": "تحليل عقد العمل", "func": "analyze_contract", "icon": "📄", "description": "تحليل عقود العمل حسب نظام العمل السعودي"},
        {"name": "حساب نهاية الخدمة", "func": "calculate_end_of_service", "icon": "💰", "description": "حساب مستحقات نهاية الخدمة"},
        {"name": "بحث قانوني", "func": "legal_search", "icon": "🔍", "description": "بحث في مواد نظام العمل"},
        {"name": "توليد مرافعة", "func": "generate_pleading", "icon": "⚖️", "description": "توليد مرافعات قانونية"},
        {"name": "كشف الغش في المراسلات", "func": "detect_deception", "icon": "🕵️", "description": "كشف التزوير أو الغش في الرسائل"},
    ],
    "employer": [
        {"name": "إنشاء عقد عمل", "func": "create_contract", "icon": "📝", "description": "إنشاء عقود عمل متوافقة مع النظام"},
        {"name": "حساب نهاية الخدمة", "func": "calculate_end_of_service", "icon": "💰", "description": "حساب مستحقات نهاية الخدمة للموظفين"},
        {"name": "بحث قانوني", "func": "legal_search", "icon": "🔍", "description": "بحث في مواد نظام العمل"},
        {"name": "تصنيف قضايا", "func": "classify_case", "icon": "🏷️", "description": "تصنيف القضايا القانونية تلقائياً"},
        {"name": "تتبع المواعيد", "func": "track_deadlines", "icon": "⏰", "description": "تتبع مواعيد تقديم الدعاوي"},
    ],
    "lawyer": [
        {"name": "بحث قانوني متقدم", "func": "legal_search", "icon": "🔍", "description": "بحث متقدم في مواد النظام"},
        {"name": "تحليل قضية", "func": "analyze_case", "icon": "📊", "description": "تحليل القضايا على 18 محوراً قانونياً"},
        {"name": "توليد مرافعة", "func": "generate_pleading", "icon": "⚖️", "description": "توليد مرافعات قانونية متقدمة"},
        {"name": "تصنيف قضايا", "func": "classify_case", "icon": "🏷️", "description": "تصنيف القضايا تلقائياً"},
        {"name": "كشف الغش", "func": "detect_deception", "icon": "🕵️", "description": "كشف التزوير في الوثائق"},
        {"name": "حساب تعويضات", "func": "calculate_compensation", "icon": "💸", "description": "حساب التعويضات القانونية"},
    ],
    "judge": [
        {"name": "تحليل قضية كامل", "func": "analyze_case", "icon": "⚖️", "description": "تحليل شامل للقضايا على 18 محوراً"},
        {"name": "بحث قانوني", "func": "legal_search", "icon": "🔍", "description": "بحث في مواد النظام"},
        {"name": "تصنيف قضايا", "func": "classify_case", "icon": "🏷️", "description": "تصنيف القضايا تلقائياً"},
        {"name": "توليد أحكام", "func": "generate_verdict", "icon": "📜", "description": "مساعدة في صياغة الأحكام"},
        {"name": "مراجعة مرافعات", "func": "review_pleading", "icon": "🔎", "description": "مراجعة المرافعات القانونية"},
    ]
}

# ======================
# TOOLS FUNCTIONS
# ======================

def get_tools_for_persona(persona: str) -> List[Dict]:
    """Get available tools for a specific persona"""
    return PERSONA_TOOLS.get(persona, [])

def get_persona_prompt(persona: str) -> str:
    """Get system prompt for a specific persona"""
    return PERSONA_PROMPTS.get(persona, "")

def get_all_personas() -> List[str]:
    """Get list of all available personas"""
    return list(PERSONA_PROMPTS.keys())

# ======================
# BASIC LEGAL TOOLS
# ======================

def analyze_contract(contract_text: str) -> Dict:
    """Analyze a contract against Saudi labor law"""
    db = get_legal_database()
    return {
        "status": "success",
        "analysis": "تحليل أولي للعقد",
        "issues": [],
        "recommendations": ["راجع المواد 40-42 لنظام العمل بشأن ساعات العمل"]
    }

def calculate_end_of_service(years: float, last_salary: float, reason: str = "استقالة") -> Dict:
    """Calculate end of service benefits"""
    if years < 2:
        return {"error": "لا يستحق العامل علاوة نهاية الخدمة إذا كانت مدة العمل أقل من عامين"}

    if reason == "استقالة":
        days = years * 15 if years <= 5 else (5 * 15 + (years - 5) * 10)
    else:  # فصل تعسفي
        days = years * 15 if years <= 5 else (5 * 15 + (years - 5) * 20)

    benefit = (last_salary / 30) * days
    return {
        "years": years,
        "last_salary": last_salary,
        "reason": reason,
        "benefit_days": days,
        "benefit_amount": round(benefit, 2),
        "calculation": f"{days} يوم × ({last_salary}/30) = {round(benefit, 2)} ريال"
    }

def legal_search(query: str, limit: int = 5) -> List[Dict]:
    """Search in legal database"""
    db = get_legal_database()
    return db.search_articles(query, limit)
