# advanced_extractor.py
"""
استخراج الكيانات المتقدمة من النصوص القانونية العمالية.
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class AdvancedExtractor:
    def extract(self, text: str) -> Dict[str, Any]:
        return {
            "personal": self._extract_personal(text),
            "employment": self._extract_employment(text),
            "financial": self._extract_financial(text),
            "legal": self._extract_legal(text),
            "timeline": self._extract_timeline(text),
            "procedural": self._extract_procedural(text),
            "risk_indicators": self._extract_risk_indicators(text),
            "full_text": text
        }

    def _extract_personal(self, text: str) -> Dict:
        # استخراج الأسماء، الهويات، العناوين
        return {
            "employee_name": self._extract_name(text, "الموظف"),
            "employer_name": self._extract_name(text, "صاحب العمل"),
            "employee_id": self._extract_id(text),
            "employer_id": self._extract_employer_id(text),
        }

    def _extract_employment(self, text: str) -> Dict:
        # استخراج بيانات التوظيف (العقد، المدة، الفصل)
        return {
            "contract_type": self._extract_contract_type(text),
            "hire_date": self._extract_hire_date(text),
            "termination_date": self._extract_termination_date(text),
            "service_years": self._extract_service_years(text),
            "position": self._extract_position(text),
        }

    def _extract_financial(self, text: str) -> Dict:
        # استخراج الرواتب، المكافآت، البدلات، الخصومات
        return {
            "basic_salary": self._extract_basic_salary(text),
            "total_salary": self._extract_total_salary(text),
            "allowances": self._extract_allowances(text),
            "deductions": self._extract_deductions(text),
            "eosb_claimed": self._extract_eosb_claimed(text),
        }

    def _extract_legal(self, text: str) -> Dict:
        # استخراج المواد القانونية المُشار إليها
        return {
            "mentioned_articles": self._extract_mentioned_articles(text),
            "mentioned_laws": self._extract_mentioned_laws(text),
        }

    def _extract_timeline(self, text: str) -> List[Dict]:
        # استخراج جميع التواريخ مع السياق
        dates = []
        for match in re.finditer(r'(\d{1,2}/\d{1,2}/\d{2,4})', text):
            date_str = match.group(1)
            context = text[max(0, match.start()-50):match.end()+50]
            dates.append({"date": date_str, "context": context})
        return dates

    def _extract_procedural(self, text: str) -> Dict:
        # استخراج الإجراءات المتخذة (تحقيق، إنذار، فصل)
        return {
            "has_investigation": "تحقيق" in text or "استجواب" in text,
            "has_warning": "إنذار" in text or "تنبيه" in text,
            "has_termination_letter": "فصل" in text or "إنهاء" in text,
            "has_appeal": "اعتراض" in text or "تظلم" in text,
        }

    def _extract_risk_indicators(self, text: str) -> List[str]:
        # كشف مؤشرات الخطر (تهديدات، تناقضات، تلاعب)
        risks = []
        if "تهديد" in text or "عقاب" in text:
            risks.append("لغة تهديدية - قد تشير إلى تعسف")
        if "بدون" in text and ("تحقيق" in text or "إنذار" in text):
            risks.append("إجراءات غير مكتملة - مخالف للنظام")
        if "رجعي" in text:
            risks.append("تطبيق رجعي - مخالف للمادة 77 من نظام العمل")
        return risks

    # ---- دوال المساعدة (اختصاراً) ----
    def _extract_name(self, text: str, role: str) -> Optional[str]:
        # محاكاة استخراج الاسم
        return None

    def _extract_id(self, text: str) -> Optional[str]:
        match = re.search(r'\b(1[0-9]{9})\b', text)
        return match.group(1) if match else None

    def _extract_employer_id(self, text: str) -> Optional[str]:
        match = re.search(r'\b([0-9]{10})\b', text)
        return match.group(1) if match else None

    def _extract_contract_type(self, text: str) -> str:
        if "محدد المدة" in text:
            return "محدد المدة"
        elif "غير محدد" in text:
            return "غير محدد المدة"
        return "غير محدد"

    def _extract_hire_date(self, text: str) -> Optional[str]:
        # استخراج تاريخ بدء العمل من سياق "بدأ العمل" أو "تاريخ الالتحاق"
        match = re.search(r'(?:بدأ|التحاق|تاريخ العمل)\s*[:]?\s*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_termination_date(self, text: str) -> Optional[str]:
        match = re.search(r'(?:فصل|إنهاء|تاريخ الفصل)\s*[:]?\s*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_service_years(self, text: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*(?:سنوات|سنة)', text, re.IGNORECASE)
        return float(match.group(1)) if match else 0.0

    def _extract_position(self, text: str) -> Optional[str]:
        match = re.search(r'(?:المهنة|الوظيفة|المسمى)\s*[:]?\s*([\u0600-\u06ff\s]+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_basic_salary(self, text: str) -> float:
        match = re.search(r'(?:الراتب الأساسي|الأساسي)\s*[:]?\s*([\d,]+)', text, re.IGNORECASE)
        return float(match.group(1).replace(',', '')) if match else 0.0

    def _extract_total_salary(self, text: str) -> float:
        match = re.search(r'(?:الراتب الإجمالي|الإجمالي)\s*[:]?\s*([\d,]+)', text, re.IGNORECASE)
        return float(match.group(1).replace(',', '')) if match else 0.0

    def _extract_allowances(self, text: str) -> Dict[str, float]:
        # محاكاة استخراج البدلات
        return {}

    def _extract_deductions(self, text: str) -> Dict[str, float]:
        # محاكاة استخراج الخصومات
        return {}

    def _extract_eosb_claimed(self, text: str) -> Optional[float]:
        match = re.search(r'(?:المكافأة|نهاية الخدمة)\s*[:]?\s*([\d,]+)', text, re.IGNORECASE)
        return float(match.group(1).replace(',', '')) if match else None

    def _extract_mentioned_articles(self, text: str) -> List[str]:
        return re.findall(r'المادة\s*([\u0660-\u0669\d]+)', text)

    def _extract_mentioned_laws(self, text: str) -> List[str]:
        return re.findall(r'(نظام\s+[\u0600-\u06ff\s]{2,30})', text)