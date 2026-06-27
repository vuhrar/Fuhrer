# discrepancy_analyzer.py
"""
محلل تناقضات التواريخ والمبالغ المستخلصة من مستندات متعددة.
يكشف أي تعارض أو تلاعب محتمل في البيانات المالية والزمنية.
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class DiscrepancyAnalyzer:
    """
    تحليل التناقضات بين التواريخ والمبالغ المستخرجة من مستندات مختلفة.
    """

    def __init__(self):
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # dd/mm/yyyy أو dd/mm/yy
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # dd-mm-yyyy
            r'\d{4}/\d{1,2}/\d{1,2}',    # yyyy/mm/dd
        ]
        self.amount_patterns = [
            r'[\d,]+\.?\d*\s*(?:ريال|ر.س|SAR|﷼)',
            r'[\d,]+\.?\d*\s*(?:دولار|USD|\$)',
        ]

    def extract_dates(self, text: str) -> List[str]:
        """استخراج جميع التواريخ من النص"""
        dates = []
        for pattern in self.date_patterns:
            dates.extend(re.findall(pattern, text))
        return dates

    def extract_amounts(self, text: str) -> List[float]:
        """استخراج جميع المبالغ المالية من النص"""
        amounts = []
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                # استخراج الرقم فقط
                num = re.search(r'[\d,]+\.?\d*', m)
                if num:
                    try:
                        amounts.append(float(num.group().replace(',', '')))
                    except ValueError:
                        pass
        return amounts

    def analyze_documents(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        تحليل مجموعة من المستندات (كل مستند يحوي 'text' و 'source').
        يعيد تقريراً بالتناقضات المكتشفة.
        """
        if not documents:
            return {"error": "لا توجد مستندات للتحليل", "discrepancies": []}

        all_dates = {}
        all_amounts = {}
        discrepancies = []

        for idx, doc in enumerate(documents):
            text = doc.get("text", "")
            source = doc.get("source", f"مستند {idx+1}")
            dates = self.extract_dates(text)
            amounts = self.extract_amounts(text)

            all_dates[source] = dates
            all_amounts[source] = amounts

        # تحليل تناقضات التواريخ
        date_discrepancies = self._analyze_date_discrepancies(all_dates)
        discrepancies.extend(date_discrepancies)

        # تحليل تناقضات المبالغ
        amount_discrepancies = self._analyze_amount_discrepancies(all_amounts)
        discrepancies.extend(amount_discrepancies)

        # تحليل تناقضات بين التواريخ والمبالغ (مثلاً: راتب وتاريخ لا يتناسبان)
        cross_discrepancies = self._analyze_cross_discrepancies(all_dates, all_amounts)
        discrepancies.extend(cross_discrepancies)

        # تقييم المخاطر الكلية
        risk_level = self._calculate_risk_level(discrepancies)

        return {
            "total_documents": len(documents),
            "discrepancies": discrepancies,
            "risk_level": risk_level,
            "summary": self._generate_summary(discrepancies, risk_level),
            "all_dates": all_dates,
            "all_amounts": all_amounts,
        }

    def _analyze_date_discrepancies(self, all_dates: Dict[str, List[str]]) -> List[Dict]:
        """
        كشف التناقضات بين التواريخ عبر المستندات المختلفة.
        """
        discrepancies = []

        # تجميع كل التواريخ مع مصادرها
        date_sources = {}
        for source, dates in all_dates.items():
            for d in dates:
                if d not in date_sources:
                    date_sources[d] = []
                date_sources[d].append(source)

        # إذا ظهر نفس التاريخ في مصدرين مختلفين، قد يكون متسقاً
        # لكن إذا كان تاريخ الفصل مختلفاً بين مستندين، فهو تناقض خطير
        termination_dates = {}
        for source, dates in all_dates.items():
            # محاولة تحديد تاريخ الفصل (عادةً آخر تاريخ في المستند)
            if dates:
                last_date = dates[-1]
                if source not in termination_dates:
                    termination_dates[source] = last_date

        # كشف التناقض في تواريخ الفصل
        if len(termination_dates) >= 2:
            unique_dates = set(termination_dates.values())
            if len(unique_dates) > 1:
                discrepancies.append({
                    "type": "date_termination_conflict",
                    "severity": "high",
                    "message": f"اختلاف تاريخ الفصل بين المستندات: {termination_dates}",
                    "details": f"تم العثور على أكثر من تاريخ فصل: {', '.join(unique_dates)}",
                    "recommendation": "يجب تحديد تاريخ الفصل الصحيح بالرجوع إلى أقرب مستند رسمي (خطاب الفصل أو شهادة الخدمة)."
                })

        # إذا كان هناك تاريخ قبل تاريخ آخر في نفس المستند
        for source, dates in all_dates.items():
            if len(dates) >= 2:
                # محاولة تحليل التواريخ
                parsed_dates = []
                for d in dates:
                    parsed = self._parse_date(d)
                    if parsed:
                        parsed_dates.append(parsed)
                if len(parsed_dates) >= 2:
                    for i in range(len(parsed_dates) - 1):
                        if parsed_dates[i] > parsed_dates[i+1]:
                            discrepancies.append({
                                "type": "date_order_conflict",
                                "severity": "medium",
                                "message": f"ترتيب زمني غير منطقي في مستند '{source}'",
                                "details": f"التاريخ {parsed_dates[i].strftime('%d/%m/%Y')} يسبق {parsed_dates[i+1].strftime('%d/%m/%Y')} في نفس المستند.",
                                "recommendation": "الترتيب الزمني غير منطقي، قد يشير إلى تلاعب أو خطأ في التوثيق."
                            })

        return discrepancies

    def _analyze_amount_discrepancies(self, all_amounts: Dict[str, List[float]]) -> List[Dict]:
        """
        كشف التناقضات في المبالغ المالية عبر المستندات.
        """
        discrepancies = []

        # جمع كل المبالغ مع مصادرها
        amount_sources = {}
        for source, amounts in all_amounts.items():
            for a in amounts:
                # تقريب لأقرب 10 ريال لتجميع المبالغ المتشابهة
                rounded = round(a / 10) * 10
                if rounded not in amount_sources:
                    amount_sources[rounded] = []
                amount_sources[rounded].append(source)

        # كشف التناقضات في الراتب الأساسي والإجمالي
        salaries = {}
        for source, amounts in all_amounts.items():
            if amounts:
                # افتراض أن أكبر مبلغ هو الراتب الإجمالي، والأصغر هو الأساسي (إن وجد)
                amounts.sort()
                if len(amounts) >= 2:
                    salaries[source] = {"basic": amounts[0], "total": amounts[-1]}
                else:
                    salaries[source] = {"basic": None, "total": amounts[0]}

        # إذا كان الراتب الإجمالي أقل من الأساسي (غير منطقي)
        for source, sal in salaries.items():
            if sal["basic"] and sal["total"] and sal["total"] < sal["basic"]:
                discrepancies.append({
                    "type": "salary_inversion",
                    "severity": "high",
                    "message": f"الراتب الإجمالي أقل من الأساسي في مستند '{source}'",
                    "details": f"الأساسي: {sal['basic']:.2f}, الإجمالي: {sal['total']:.2f}",
                    "recommendation": "هذا غير منطقي مادياً، قد يكون هناك خطأ في قراءة المبالغ أو تلاعب."
                })

        # اختلاف الرواتب بين المستندات
        salary_values = [s["total"] for s in salaries.values() if s["total"]]
        if len(salary_values) >= 2 and len(set(salary_values)) > 1:
            discrepancies.append({
                "type": "salary_conflict",
                "severity": "high",
                "message": f"اختلاف في قيمة الراتب الإجمالي بين المستندات: {salary_values}",
                "details": f"الرواتب المكتشفة: {', '.join([f'{v:.2f}' for v in salary_values])}",
                "recommendation": "يجب التحقق من الراتب الصحيح من عقد العمل أو كشف الراتب المعتمد."
            })

        return discrepancies

    def _analyze_cross_discrepancies(self, all_dates: Dict[str, List[str]], all_amounts: Dict[str, List[float]]) -> List[Dict]:
        """
        تحليل التناقضات المتقاطعة (مثلاً: مدة الخدمة لا تتوافق مع المكافأة المحسوبة).
        """
        discrepancies = []

        # إذا كان هناك تواريخ ومبالغ في نفس المستند
        for source in set(all_dates.keys()) & set(all_amounts.keys()):
            dates = all_dates.get(source, [])
            amounts = all_amounts.get(source, [])
            if dates and amounts:
                # محاولة حساب المدة من التواريخ
                parsed_dates = [self._parse_date(d) for d in dates if self._parse_date(d)]
                if len(parsed_dates) >= 2:
                    start = min(parsed_dates)
                    end = max(parsed_dates)
                    service_days = (end - start).days
                    service_years = service_days / 365.25

                    # إذا كانت المدة أكثر من 5 سنوات، يجب أن يكون الراتب كبيراً نسبياً
                    if service_years > 5 and max(amounts) < 5000:
                        discrepancies.append({
                            "type": "service_amount_mismatch",
                            "severity": "medium",
                            "message": f"مدة خدمة طويلة ({service_years:.1f} سنة) مع راتب منخفض ({max(amounts):.2f}) في '{source}'",
                            "details": f"قد يشير إلى خطأ في قراءة الراتب أو مدة الخدمة.",
                            "recommendation": "تحقق من صحة مدة الخدمة والراتب الموثقين."
                        })

        return discrepancies

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        محاولة تحويل سلسلة نصية إلى كائن datetime.
        """
        for fmt in ["%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%d-%m-%Y", "%d-%m-%y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def _calculate_risk_level(self, discrepancies: List[Dict]) -> str:
        """
        حساب مستوى المخاطر بناءً على التناقضات المكتشفة.
        """
        if not discrepancies:
            return "منخفضة (لا توجد تناقضات مكتشفة)"
        high_count = sum(1 for d in discrepancies if d.get("severity") == "high")
        medium_count = sum(1 for d in discrepancies if d.get("severity") == "medium")
        if high_count >= 2:
            return "عالية جداً (تناقضات خطيرة متعددة)"
        elif high_count >= 1:
            return "عالية (يوجد تناقض خطير واحد على الأقل)"
        elif medium_count >= 3:
            return "متوسطة (تناقضات متعددة متوسطة الأهمية)"
        elif medium_count >= 1:
            return "متوسطة (يوجد تناقض متوسط الأهمية)"
        else:
            return "منخفضة (تناقضات طفيفة أو لا توجد)"

    def _generate_summary(self, discrepancies: List[Dict], risk_level: str) -> str:
        """
        توليد ملخص للتناقضات.
        """
        if not discrepancies:
            return "✅ لم يتم العثور على أي تناقضات في المستندات التي تم تحليلها."

        summary = f"⚠️ تم العثور على {len(discrepancies)} تناقض(ات). مستوى المخاطر: {risk_level}\n"
        for d in discrepancies[:5]:
            summary += f"• {d.get('message', '')}\n"
        if len(discrepancies) > 5:
            summary += f"... و {len(discrepancies) - 5} تناقضات إضافية."
        return summary