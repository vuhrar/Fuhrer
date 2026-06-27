# procedural_analyzer.py
"""
محلل صحة الإجراءات الإدارية وفق نظام العمل السعودي.
يتحقق من استيفاء صاحب العمل للشروط النظامية (التحقيق، الإنذار، المهلة)
قبل اتخاذ قرار الفصل.
"""
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

class ProceduralAnalyzer:
    """
    تحليل الإجراءات الإدارية المتخذة من قبل صاحب العمل.
    """

    def __init__(self):
        # المواد النظامية المرجعية
        self.ARTICLE_80 = "المادة 80 من نظام العمل (الفصل التأديبي)"
        self.ARTICLE_81 = "المادة 81 من نظام العمل (الفصل التعسفي)"
        self.ARTICLE_75 = "المادة 75 من نظام العمل (مهلة الإشعار)"

    def analyze(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        تحليل صحة الإجراءات الإدارية في النص المقدم.
        """
        context = context or {}
        results = {
            "has_investigation": self._check_investigation(text),
            "has_notice": self._check_notice(text),
            "notice_period_days": self._extract_notice_period(text),
            "has_termination_letter": self._check_termination_letter(text),
            "has_warning": self._check_warning(text),
            "is_arbitrary": False,
            "violations": [],
            "recommendations": [],
            "legal_references": [],
        }

        # تحليل نوع الفصل
        results["is_arbitrary"] = self._check_arbitrary_dismissal(text, results)

        # تحديد المخالفات
        violations = self._identify_violations(text, results)
        results["violations"] = violations

        # توليد التوصيات
        results["recommendations"] = self._generate_recommendations(results)

        # المراجع القانونية
        results["legal_references"] = self._generate_legal_references(results)

        return results

    def _check_investigation(self, text: str) -> bool:
        """
        التحقق من وجود إشارة إلى تحقيق رسمي قبل الفصل.
        """
        investigation_keywords = [
            "تحقيق", "استجواب", "سماع أقوال", "دفاع", "محضر", "لجنة", "تحقيق إداري"
        ]
        for kw in investigation_keywords:
            if kw in text:
                return True
        return False

    def _check_notice(self, text: str) -> bool:
        """
        التحقق من وجود إشعار بالفصل أو مهلة.
        """
        notice_keywords = [
            "إشعار", "إنذار", "مهلة", "إخطار", "تبليغ", "علمك", "نحيطكم"
        ]
        for kw in notice_keywords:
            if kw in text:
                return True
        return False

    def _extract_notice_period(self, text: str) -> Optional[int]:
        """
        محاولة استخراج مدة الإشعار بالأيام من النص.
        """
        patterns = [
            r'(\d+)\s*(?:يوم|أيام|شهر|أشهر)',
            r'(\d+)\s*يوم',
            r'(\d+)\s*شهر',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = int(match.group(1))
                    if 'شهر' in match.group(0):
                        return value * 30  # تقريباً
                    return value
                except ValueError:
                    pass
        return None

    def _check_termination_letter(self, text: str) -> bool:
        """
        التحقق من وجود خطاب فصل رسمي.
        """
        termination_keywords = [
            "فصل", "إنهاء الخدمة", "إنهاء عقد", "خطاب فصل", "قرار فصل",
            "تم فصلك", "تنتهي علاقتك"
        ]
        for kw in termination_keywords:
            if kw in text:
                return True
        return False

    def _check_warning(self, text: str) -> bool:
        """
        التحقق من وجود إنذار سابق قبل الفصل.
        """
        warning_keywords = [
            "إنذار", "تنبيه", "تحذير", "إنذار أول", "إنذار ثانٍ", "آخر إنذار"
        ]
        for kw in warning_keywords:
            if kw in text:
                return True
        return False

    def _check_arbitrary_dismissal(self, text: str, results: Dict) -> bool:
        """
        تحديد ما إذا كان الفصل تعسفياً.
        """
        # إذا لم يكن هناك تحقيق وفصل مباشر
        if not results["has_investigation"] and results["has_termination_letter"]:
            return True
        # إذا لم يكن هناك إنذار سابق
        if not results["has_warning"] and results["has_termination_letter"]:
            return True
        # إذا كانت مدة الإشعار أقل من النظامية
        if results["notice_period_days"] and results["notice_period_days"] < 15:
            return True
        return False

    def _identify_violations(self, text: str, results: Dict) -> List[Dict]:
        """
        تحديد المخالفات الإجرائية المحددة.
        """
        violations = []

        # 1. الفصل بدون تحقيق
        if results["has_termination_letter"] and not results["has_investigation"]:
            violations.append({
                "type": "no_investigation",
                "severity": "high",
                "message": "الفصل تم دون تحقيق مسبق (مخالف للمادة 80 من نظام العمل)",
                "legal_reference": "المادة 80 من نظام العمل",
                "impact": "يُعتبر الفصل باطلاً ويستوجب التعويض."
            })

        # 2. الفصل بدون إنذار
        if results["has_termination_letter"] and not results["has_warning"]:
            violations.append({
                "type": "no_warning",
                "severity": "medium",
                "message": "الفصل تم دون إنذار سابق (مخالف للإجراءات النظامية)",
                "legal_reference": "المادة 80 من نظام العمل",
                "impact": "يُعتبر الفصل غير قانوني ويُمكن الطعن عليه."
            })

        # 3. مهلة الإشعار غير كافية
        if results["notice_period_days"] and results["notice_period_days"] < 15:
            violations.append({
                "type": "insufficient_notice",
                "severity": "medium",
                "message": f"مدة الإشعار ({results['notice_period_days']} يوم) أقل من الحد الأدنى النظامي (15 يوم)",
                "legal_reference": "المادة 75 من نظام العمل",
                "impact": "يستحق العامل تعويضاً عن المدة المتبقية من الإشعار."
            })

        # 4. الفصل التعسفي
        if results["is_arbitrary"]:
            violations.append({
                "type": "arbitrary_dismissal",
                "severity": "high",
                "message": "فصل تعسفي (مخالف للمادة 81 من نظام العمل)",
                "legal_reference": "المادة 81 من نظام العمل",
                "impact": "يستوجب تعويضاً يصل إلى راتب سنة كاملة."
            })

        return violations

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """
        توليد توصيات بناءً على المخالفات المكتشفة.
        """
        recommendations = []
        if results.get("is_arbitrary"):
            recommendations.append("⚖️ يُنصح برفع دعوى فصل تعسفي للمطالبة بالتعويض.")
        if not results.get("has_investigation") and results.get("has_termination_letter"):
            recommendations.append("📋 يُنصح بتقديم اعتراض رسمي لدى مكتب العمل لإثبات بطلان الفصل.")
        if results.get("notice_period_days") and results.get("notice_period_days") < 15:
            recommendations.append("💰 يُنصح بالمطالبة بتعويض عن مدة الإشعار غير المكتملة.")
        if not recommendations:
            recommendations.append("✅ الإجراءات تبدو سليمة من الناحية الشكلية. يُنصح بمراجعة مستندات إضافية.")
        return recommendations

    def _generate_legal_references(self, results: Dict) -> List[str]:
        """
        توليد المراجع القانونية ذات الصلة.
        """
        refs = []
        if results.get("is_arbitrary"):
            refs.append("المادة (81) من نظام العمل - الفصل التعسفي")
        if not results.get("has_investigation"):
            refs.append("المادة (80) من نظام العمل - اشتراط التحقيق قبل الفصل")
        if results.get("notice_period_days") and results.get("notice_period_days") < 15:
            refs.append("المادة (75) من نظام العمل - مهلة الإشعار")
        return refs
