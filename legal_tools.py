# legal_tools.py - Legal Tools Module for Fuhrer App

from typing import Dict, List, Callable, Optional
import streamlit as st
from legal_database import get_legal_database

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
# TOOLS FUNCTION
# ======================

def get_tools_for_persona(persona: str) -> List[Dict]:
    """
    Get available tools for a specific persona

    Args:
        persona: One of ['worker', 'employer', 'lawyer', 'judge']

    Returns:
        List of tool dictionaries with name, func, icon, description
    """
    return PERSONA_TOOLS.get(persona, [])

def get_all_personas() -> List[str]:
    """Get list of all available personas"""
    return list(PERSONA_TOOLS.keys())

# ======================
# BASIC LEGAL TOOLS
# ======================

def analyze_contract(contract_text: str) -> Dict:
    """Analyze a contract against Saudi labor law"""
    db = get_legal_database()
    # Basic implementation - will be enhanced in legal_tools_advanced.py
    return {
        "status": "success",
        "analysis": "تحليل أولي للعقد",
        "issues": [],
        "recommendations": ["راجع المواد 40-42 لنظام العمل بشأن ساعات العمل"]
    }

def calculate_end_of_service(years: float, last_salary: float, reason: str = "استقالة") -> Dict:
    """Calculate end of service benefits"""
    # Basic calculation
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

# Add more basic tools as needed...
