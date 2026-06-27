# labor_calculator.py
"""
حاسبة المستحقات العمالية وفق نظام العمل السعودي.
تحسب المكافأة، التعويض، المتأخرات، وصافي المقبوض.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LaborCalculator:
    """حاسبة المستحقات العمالية"""

    def __init__(self, basic_salary: float = 0, total_salary: float = 0, service_years: float = 0,
                 absence_days: int = 0, salary_delay_months: int = 0, is_arbitrary_dismissal: bool = False,
                 has_contract: bool = True, is_saudi: bool = True):
        self.basic_salary = basic_salary
        self.total_salary = total_salary if total_salary > 0 else basic_salary
        self.service_years = service_years
        self.absence_days = absence_days
        self.salary_delay_months = salary_delay_months
        self.is_arbitrary_dismissal = is_arbitrary_dismissal
        self.has_contract = has_contract
        self.is_saudi = is_saudi

    def calculate_eosb(self) -> Dict[str, Any]:
        """
        حساب مكافأة نهاية الخدمة (المادة 84)
        - أول 5 سنوات: نصف شهر عن كل سنة.
        - ما بعد 5 سنوات: شهر كامل عن كل سنة.
        """
        if self.service_years <= 0:
            return {"amount": 0, "formula": "مدة الخدمة أقل من سنة، لا تستحق مكافأة.", "details": []}

        details = []
        total = 0
        years_5 = min(self.service_years, 5)
        years_after = max(0, self.service_years - 5)

        if years_5 > 0:
            amount_5 = (self.basic_salary / 2) * years_5
            total += amount_5
            details.append(f"السنوات الخمس الأولى ({years_5} سنة) × نصف شهر = {amount_5:,.2f} ريال")

        if years_after > 0:
            amount_after = self.basic_salary * years_after
            total += amount_after
            details.append(f"السنوات التالية ({years_after} سنة) × شهر كامل = {amount_after:,.2f} ريال")

        # خصم أيام الغياب (إن وجدت) - يخصم بعد أول 15 يوم غياب
        deduction = 0
        if self.absence_days > 15:
            deduction = (self.basic_salary / 30) * (self.absence_days - 15)
            details.append(f"خصم أيام الغياب ({self.absence_days - 15} يوم) = -{deduction:,.2f} ريال")

        # خصم في حالة الاستقالة (إذا لم تكن مكافأة كاملة)
        # يفترض هنا أن الحاسبة تعرف نوع الإنهاء، لكننا سنتركها للمستخدم لتحديدها

        net = total - deduction
        return {
            "amount": round(net, 2),
            "gross": round(total, 2),
            "deduction": round(deduction, 2),
            "formula": "نصف شهر عن كل سنة من السنوات الخمس الأولى، وشهر كامل عن كل سنة تالية (المادة 84).",
            "details": details,
            "legal_reference": "المادة (84) من نظام العمل"
        }

    def calculate_arbitrary_compensation(self) -> Dict[str, Any]:
        """
        حساب تعويض الفصل التعسفي (المادة 77 و 81)
        الحد الأعلى: راتب سنة كاملة (12 شهراً)
        """
        if not self.is_arbitrary_dismissal:
            return {"amount": 0, "message": "لا يوجد فصل تعسفي.", "legal_reference": "المادة (77) من نظام العمل"}

        max_compensation = self.total_salary * 12
        # في حالة الفصل التعسفي، يستحق الحد الأعلى إذا كانت المدة طويلة
        # نعطي تقديراً بناءً على المدة (حد أدنى 3 شهور، حد أقصى 12 شهراً)
        months = min(12, max(3, int(self.service_years * 0.8)))
        estimated = self.total_salary * months

        return {
            "amount": round(estimated, 2),
            "max_limit": round(max_compensation, 2),
            "months": months,
            "formula": f"{months} شهر × الراتب الإجمالي ({self.total_salary:,.2f})",
            "legal_reference": "المادة (77) و (81) من نظام العمل",
            "message": f"التعويض المقدر عن الفصل التعسفي (حد أعلى {max_compensation:,.2f} ريال)"
        }

    def calculate_salary_delay(self) -> Dict[str, Any]:
        """حساب تعويض تأخير الراتب"""
        if self.salary_delay_months <= 0:
            return {"amount": 0, "message": "لا يوجد تأخير في الراتب."}

        # التأخير الشهري يحسب بواقع 5% من الراتب عن كل شهر تأخير (وفقاً للقضاء العمالي)
        delay_compensation = self.total_salary * 0.05 * self.salary_delay_months
        return {
            "amount": round(delay_compensation, 2),
            "months": self.salary_delay_months,
            "formula": f"{self.salary_delay_months} شهر × 5%",
            "legal_reference": "المادة (90) من نظام العمل (حقوق العامل في الأجور)",
            "message": f"تعويض تأخير الراتب عن {self.salary_delay_months} شهر"
        }

    def calculate_total_entitlement(self) -> Dict[str, Any]:
        """حساب إجمالي المستحقات"""
        eosb = self.calculate_eosb()
        compensation = self.calculate_arbitrary_compensation() if self.is_arbitrary_dismissal else {"amount": 0}
        delay = self.calculate_salary_delay()

        total = eosb["amount"] + compensation["amount"] + delay["amount"]

        # خصم التأمينات الاجتماعية (9% للموظف السعودي)
        gosi_deduction = self.total_salary * 0.09 if self.is_saudi else 0

        net_total = total - gosi_deduction

        return {
            "total_gross": round(total, 2),
            "total_net": round(net_total, 2),
            "eosb": eosb,
            "arbitrary_compensation": compensation,
            "salary_delay": delay,
            "gosi_deduction": round(gosi_deduction, 2),
            "summary": f"إجمالي المستحقات (الإجمالي): {total:,.2f} ريال | (الصافي): {net_total:,.2f} ريال"
        }