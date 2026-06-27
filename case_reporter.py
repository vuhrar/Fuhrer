# case_reporter.py
"""
توليد التقارير الأربعة (مالي، إداري، استراتيجي، قضائي).
"""
from typing import Dict, Any
from datetime import datetime

class CaseReporter:
    def generate_financial_report(self, data: Dict) -> str:
        """تقرير مالي"""
        return f"""
        التقرير المالي
        التاريخ: {datetime.now().strftime('%d/%m/%Y')}

        الراتب الأساسي: {data.get('basic_salary', 0):,.2f} ريال
        الراتب الإجمالي: {data.get('total_salary', 0):,.2f} ريال
        مدة الخدمة: {data.get('service_years', 0):.2f} سنة

        المكافأة المستحقة: {data.get('eosb', 0):,.2f} ريال
        التعويض عن الفصل التعسفي: {data.get('compensation', 0):,.2f} ريال
        المتأخرات: {data.get('delays', 0):,.2f} ريال
        صافي المستحق: {data.get('net', 0):,.2f} ريال

        المراجع القانونية: المادة 84، المادة 81، المادة 77
        """

    def generate_administrative_report(self, data: Dict) -> str:
        """تقرير إداري"""
        return f"""
        التقرير الإداري

        الإجراءات المتخذة:
        - تحقيق: {'تم' if data.get('has_investigation') else 'لم يتم'}
        - إنذار سابق: {'تم' if data.get('has_warning') else 'لم يتم'}
        - خطاب فصل: {'موجود' if data.get('has_termination_letter') else 'غير موجود'}

        التوصيات:
        - {'إعادة النظر في إجراءات الفصل' if not data.get('has_investigation') else 'الإجراءات سليمة'}
        - {'تقديم اعتراض لمكتب العمل' if not data.get('has_warning') else 'لا حاجة'}
        """

    def generate_strategic_report(self, data: Dict) -> str:
        """تقرير استراتيجي"""
        return f"""
        التقرير الاستراتيجي

        نقاط القوة:
        - {'مواد قانونية واضحة' if data.get('laws') else 'لا توجد مواد واضحة'}
        - {'أدلة مؤيدة' if data.get('evidence') else 'لا توجد أدلة'}

        نقاط الضعف:
        - {'ضعف الأدلة' if not data.get('evidence') else 'لا توجد نقاط ضعف واضحة'}
        - {'مخاطر التقادم' if data.get('statute_risk') else 'لا توجد'}

        التوصية الاستراتيجية:
        - {'تقاضي' if data.get('case_strength') == 'قوية' else 'صلح'}
        """

    def generate_judicial_report(self, data: Dict) -> str:
        """تقرير قضائي (صحيفة دعوى)"""
        return f"""
        صحيفة دعوى

        المدعي: {data.get('plaintiff', 'غير محدد')}
        المدعى عليه: {data.get('defendant', 'غير محدد')}

        الوقائع:
        {data.get('facts', 'لم يتم تحديدها')}

        الطلبات:
        1. إلزام المدعى عليه بدفع {data.get('claim_amount', 0):,.2f} ريال.
        2. التعويض عن الأضرار المادية والمعنوية.
        3. المصاريف القضائية.

        المستندات المؤيدة:
        {data.get('attachments', 'لا توجد مستندات')}

        المراجع القانونية:
        {data.get('laws', 'لا توجد مراجع')}
        """