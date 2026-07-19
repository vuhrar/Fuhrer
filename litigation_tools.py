"""
مركز المنازعات 
أدوات قانونية  مبنية على نظام العمل السعودي ونظام المرافعات الشرعية
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# ============================================================
# ١. محلل الأدلة والإثبات
# ============================================================
class EvidenceAnalyzer:
    """
    تحليل وتقييم الأدلة في المنازعات العمالية وفقاً لنظام الإثبات.
    يصنف الأدلة حسب قوتها القانونية ويحسب الدرجة الإجمالية.
    """

    EVIDENCE_TYPES = {
        "مستند رسمي حكومي":       {"weight": 10, "desc": "أعلى درجات الإثبات — خطاب رسمي، حكم سابق، شهادة GOSI"},
        "عقد عمل موثق":            {"weight": 9, "desc": "عقد موقع من الطرفين وموثق لدى الوزارة"},
        "إشعار كتابي مثبت بالاستلام": {"weight": 8, "desc": "إشعار إنهاء، إنذار، مراسلة رسمية بشرط إثبات الاستلام"},
        "كشف راتب بنكي":           {"weight": 8, "desc": "دليل قاطع على الأجر الفعلي"},
        "بريد إلكتروني رسمي":       {"weight": 6, "desc": "بريد عمل رسمي مع إيصال قراءة"},
        "رسالة واتساب/نصية":        {"weight": 4, "desc": "قد تُقبل كقرينة إذا كانت واضحة وغير منقطعة"},
        "شهادة شاهد واحد":          {"weight": 3, "desc": "شهادة الشهود مقبولة مع قرائن أخرى"},
        "شهادة شاهدين":             {"weight": 6, "desc": "شاهدان يعززان بعضهما"},
        "تسجيل صوتي":              {"weight": 5, "desc": "قد يُقبل إذا لم يكن فيه انتهاك للخصوصية"},
        "صورة/لقطة شاشة":          {"weight": 3, "desc": "تُقبل كقرينة معززة فقط"},
        "محضر تحقيق داخلي":         {"weight": 7, "desc": "وثيقة تحقيق موقعة من أطراف متعددة"},
        "تقرير طبي رسمي":          {"weight": 9, "desc": "في إصابات العمل — دليل قاطع"},
    }

    def analyze_evidence(self, evidence_list: List[Dict]) -> Dict:
        total = 0
        details = []
        types_found = set()

        for ev in evidence_list:
            etype = ev.get("type", "")
            info = self.EVIDENCE_TYPES.get(etype)
            if info:
                weight = info["weight"]
                total += weight
                types_found.add(etype)
                details.append({
                    "type": etype,
                    "description": ev.get("description", ""),
                    "weight": weight,
                    "note": info["desc"],
                    "date": ev.get("date", ""),
                })

        percentage = min(100, round((total / (len(evidence_list) * 10)) * 100)) if evidence_list else 0

        if percentage >= 75:
            category, color, recommendation = "قوي جداً", "#4ade80", "✅ موقف قوي — يمكن المطالبة بالحد الأعلى والتوجه مباشرة للمحكمة"
        elif percentage >= 50:
            category, color, recommendation = "جيد", "#4a9eff", "👍 موقف جيد — يُنصح بجمع المزيد من الأدلة ثم رفع الدعوى"
        elif percentage >= 30:
            category, color, recommendation = "متوسط", "#ffb400", "⚠️ موقف متوسط — يُنصح بالتسوية الودية قبل اللجوء للمحكمة"
        else:
            category, color, recommendation = "ضعيف", "#ff5a5a", "❌ موقف ضعيف — يُنصح بتعزيز الأدلة قبل أي إجراء قضائي"

        recommended_evidence = [
            "عقد عمل موثق", "إشعار كتابي مثبت بالاستلام", "كشف راتب بنكي",
            "محضر تحقيق داخلي", "شهادة شاهدين"
        ]
        gaps = [r for r in recommended_evidence if r not in types_found]

        return {
            "total_score": total,
            "evidence_count": len(evidence_list),
            "percentage": percentage,
            "category": category,
            "color": color,
            "recommendation": recommendation,
            "details": details,
            "gaps": gaps,
        }

    def check_evidence_gaps(self, case_type: str) -> List[Dict]:
        required = {
            "فصل تعسفي": [
                {"type": "إشعار كتابي مثبت بالاستلام", "priority": "أساسي", "note": "إثبات الفصل"},
                {"type": "كشف راتب بنكي", "priority": "أساسي", "note": "إثبات الأجر للتعويض"},
                {"type": "عقد عمل موثق", "priority": "أساسي", "note": "إثبات العلاقة العمالية"},
                {"type": "رسالة واتساب/نصية", "priority": "ثانوي", "note": "سبب الفصل"},
            ],
            "نهاية الخدمة": [
                {"type": "عقد عمل موثق", "priority": "أساسي", "note": "تاريخ بداية ونهاية العمل"},
                {"type": "كشف راتب بنكي", "priority": "أساسي", "note": "حساب المكافأة"},
                {"type": "مستند رسمي حكومي", "priority": "ثانوي", "note": "شهادة GOSI"},
            ],
            "تأخير راتب": [
                {"type": "كشف راتب بنكي", "priority": "أساسي", "note": "إثبات عدم الصرف"},
                {"type": "رسالة واتساب/نصية", "priority": "ثانوي", "note": "مراسلات المطالبة"},
                {"type": "عقد عمل موثق", "priority": "أساسي", "note": "إثبات الأجر المتفق عليه"},
            ],
            "إصابة عمل": [
                {"type": "تقرير طبي رسمي", "priority": "أساسي", "note": "إثبات الإصابة"},
                {"type": "مستند رسمي حكومي", "priority": "أساسي", "note": "بلاغ إصابة عمل"},
                {"type": "شهادة شاهدين", "priority": "ثانوي", "note": "شهود على الحادث"},
            ],
        }
        return required.get(case_type, required.get("فصل تعسفي", []))

# ============================================================
# ٢. حاسبة التسوية ومقارنة التقاضي
# ============================================================
class SettlementCalculator:
    """حساب نطاق التسوية المقبول ومقارنته بتكاليف وإجراءات التقاضي."""

    SETTLEMENT_RANGES = {
        "نهاية الخدمة":    {"min_percent": 70, "max_percent": 95, "note": "حقوق ثابتة — التسوية قريبة من كامل المبلغ"},
        "فصل تعسفي":       {"min_percent": 40, "max_percent": 80, "note": "تقديرية — نطاق تفاوضي واسع"},
        "الأجور والرواتب":  {"min_percent": 80, "max_percent": 100, "note": "حقوق ثابتة — صعوبة في التنازل"},
        "تأخير راتب":       {"min_percent": 70, "max_percent": 100, "note": "قد يُضاف تعويض تأخير"},
        "إصابة عمل":        {"min_percent": 50, "max_percent": 90, "note": "تقديرية — تعتمد على نسبة العجز"},
        "الإجازات":         {"min_percent": 60, "max_percent": 100, "note": "قد تُحسب كبدل نقدي"},
        "ساعات العمل":      {"min_percent": 50, "max_percent": 90, "note": "أجر إضافي + تعويض"},
    }

    def calculate_settlement_range(self, total_claim: float, case_type: str) -> Dict:
        info = self.SETTLEMENT_RANGES.get(case_type, {"min_percent": 50, "max_percent": 80, "note": "تقديري"})

        min_settlement = total_claim * (info["min_percent"] / 100)
        max_settlement = total_claim * (info["max_percent"] / 100)
        mid_settlement = (min_settlement + max_settlement) / 2

        litigation_time = self._estimate_litigation_time(case_type)
        litigation_cost = self._estimate_litigation_cost(total_claim)

        net_lit = round(total_claim * 0.85 - litigation_cost["total"], 2)
        net_settle = round(mid_settlement, 2)

        if net_settle >= net_lit * 0.85:
            rec = "🤝 **التسوية الودية أفضل** — ستحصل على مبلغ قريب جداً من العائد المتوقع من المحكمة، مع توفير الوقت والجهد والتكاليف"
        elif net_settle >= net_lit * 0.6:
            rec = "⚖️ **خيار متوازن** — يمكن قبول التسوية إذا كنت تفضل السرعة، أو المتابعة قضائياً إذا كنت مستعداً للانتظار"
        else:
            rec = "🏛️ **المتابعة القضائية أفضل** — مبلغ التسوية منخفض مقارنة بالعائد المتوقع من المحكمة"

        return {
            "total_claim": round(total_claim, 2),
            "case_type": case_type,
            "min_settlement": round(min_settlement, 2),
            "max_settlement": round(max_settlement, 2),
            "recommended_settlement": round(mid_settlement, 2),
            "settlement_note": info["note"],
            "litigation_time": litigation_time,
            "litigation_cost": litigation_cost,
            "net_litigation": net_lit,
            "recommendation": rec,
        }

    def _estimate_litigation_time(self, case_type: str) -> Dict:
        times = {
            "نهاية الخدمة":    {"min_months": 3, "max_months": 8, "avg_months": 5},
            "فصل تعسفي":       {"min_months": 4, "max_months": 12, "avg_months": 7},
            "الأجور والرواتب":  {"min_months": 2, "max_months": 6, "avg_months": 4},
            "إصابة عمل":        {"min_months": 6, "max_months": 18, "avg_months": 10},
            "الإجازات":         {"min_months": 2, "max_months": 5, "avg_months": 3},
        }
        return times.get(case_type, {"min_months": 3, "max_months": 9, "avg_months": 6})

    def _estimate_litigation_cost(self, claim_amount: float) -> Dict:
        lawyer_fee = max(5000, claim_amount * 0.10)
        admin_cost = 1500
        time_cost = 3000
        return {
            "lawyer_fee": round(lawyer_fee, 2),
            "admin_cost": admin_cost,
            "time_cost": time_cost,
            "total": round(lawyer_fee + admin_cost + time_cost, 2),
            "note": "تقديري — المحاكم العمالية مجانية لكن هناك تكاليف محاماة ومصاريف غير مباشرة"
        }

# ============================================================
# ٣. المخطط الزمني لإجراءات التقاضي
# ============================================================
class LitigationTimeline:
    """المخطط الزمني لإجراءات التقاضي العمالي في السعودية."""

    STAGES = [
        {
            "stage": 1, "name": "تقديم الشكوى لوزارة الموارد البشرية",
            "icon": "📨",
            "duration_days": 1, "duration_text": "يوم واحد",
            "description": "تقديم شكوى عبر بوابة وزارة الموارد البشرية أو تطبيق 'ودي' للمنازعات العمالية",
            "action": "تجهيز: الهوية، عقد العمل، كشوف الرواتب، المستندات الداعمة",
            "outcome": "رقم مرجعي للشكوى",
            "article": "م 209",
        },
        {
            "stage": 2, "name": "محاولة التسوية الودية",
            "icon": "🤝",
            "duration_days": 21, "duration_text": "حتى 21 يوم",
            "description": "الوزارة تتواصل مع صاحب العمل لمحاولة التسوية الودية",
            "action": "انتظار — قد يطلب منك تقديم مستندات إضافية",
            "outcome": "إما تسوية أو إحالة للمحكمة العمالية",
            "article": "م 210",
        },
        {
            "stage": 3, "name": "رفع الدعوى للمحكمة العمالية",
            "icon": "⚖️",
            "duration_days": 1, "duration_text": "يوم واحد",
            "description": "تقديم لائحة الدعوى إلكترونياً عبر بوابة المحكمة العمالية (ناجز)",
            "action": "صياغة لائحة دعوى محكمة مع ذكر الوقائع والمطالبات والمواد النظامية",
            "outcome": "تحديد موعد أول جلسة (عادة خلال 30-60 يوم)",
            "article": "م 212",
        },
        {
            "stage": 4, "name": "الجلسة الأولى — تبادل المذكرات",
            "icon": "📋",
            "duration_days": 30, "duration_text": "حتى 30 يوم",
            "description": "الجلسة الأولى: تقديم لائحة الدعوى، ورد المدعى عليه بمذكرة جوابية",
            "action": "احضر الجلسة شخصياً أو عبر وكيل. قدم الأدلة الأصلية.",
            "outcome": "تحديد نقاط الخلاف وجدولة جلسات الإثبات",
            "article": "",
        },
        {
            "stage": 5, "name": "جلسات الإثبات والمرافعة",
            "icon": "🔍",
            "duration_days": 60, "duration_text": "30-90 يوم",
            "description": "تقديم الأدلة، سماع الشهود، المرافعات الشفهية والكتابية",
            "action": "قدم كل الأدلة. استدعِ الشهود. قدم مذكرة ختامية.",
            "outcome": "حجز القضية للحكم",
            "article": "",
        },
        {
            "stage": 6, "name": "النطق بالحكم الابتدائي",
            "icon": "📜",
            "duration_days": 30, "duration_text": "حتى 30 يوم",
            "description": "تصدر المحكمة حكمها الابتدائي",
            "action": "استلام نسخة الحكم ودراسته",
            "outcome": "حكم ابتدائي — لأي طرف 30 يوماً للاستئناف",
            "article": "",
        },
        {
            "stage": 7, "name": "الاستئناف (اختياري)",
            "icon": "📤",
            "duration_days": 90, "duration_text": "60-120 يوم",
            "description": "إذا استأنف أي طرف، تنظر محكمة الاستئناف في القضية",
            "action": "تقديم لائحة استئنافية خلال 30 يوماً من الحكم الابتدائي",
            "outcome": "حكم نهائي من محكمة الاستئناف",
            "article": "",
        },
        {
            "stage": 8, "name": "تنفيذ الحكم",
            "icon": "✅",
            "duration_days": 30, "duration_text": "حتى 30 يوم",
            "description": "تقديم طلب تنفيذ الحكم لدى محكمة التنفيذ",
            "action": "إذا لم يمتثل الطرف المحكوم عليه، قدم طلب تنفيذ",
            "outcome": "إجبار المحكوم عليه على التنفيذ",
            "article": "",
        },
    ]

    def get_full_timeline(self, case_type: str) -> Dict:
        total_min_days = sum(s["duration_days"] for s in self.STAGES)

        first_stage_notes = {
            "فصل تعسفي": "اذكر في الشكوى: تاريخ الفصل، سببه إن وجد، والمطالبة بالتعويض وفق م 77",
            "نهاية الخدمة": "اذكر: تاريخ انتهاء العقد، المسمى الوظيفي، الراتب الأساسي والإجمالي",
            "تأخير راتب": "اذكر: الأشهر المتأخرة، المبالغ، تواريخ الاستحقاق",
            "إصابة عمل": "ارفق: التقرير الطبي، بلاغ الشرطة إن وجد، إثبات العلاقة العمالية",
        }

        return {
            "case_type": case_type,
            "stages": self.STAGES,
            "total_estimated_months": round(total_min_days / 30, 1),
            "from_start_to_judgment_months": round(sum(s["duration_days"] for s in self.STAGES[:6]) / 30, 1),
            "first_stage_note": first_stage_notes.get(case_type, ""),
            "important_note": "⚠️ المدد تقديرية وتختلف حسب ظروف كل قضية وضغط العمل في المحاكم",
        }

    def get_current_stage_info(self, case_type: str, days_since_filing: int) -> Dict:
        cumulative = 0
        current_stage = None
        next_stage = None

        for stage in self.STAGES:
            if days_since_filing <= cumulative + stage["duration_days"]:
                current_stage = stage
                idx = self.STAGES.index(stage)
                next_stage = self.STAGES[idx + 1] if idx + 1 < len(self.STAGES) else None
                break
            cumulative += stage["duration_days"]

        if current_stage is None:
            current_stage = self.STAGES[-1]

        return {
            "days_since_filing": days_since_filing,
            "current_stage": current_stage,
            "next_stage": next_stage,
            "progress_percent": min(100, round((days_since_filing / self.get_full_timeline(case_type)["total_estimated_months"] / 30 * 100) if self.get_full_timeline(case_type)["total_estimated_months"] > 0 else 100)),
        }

# ============================================================
# ٤. مولد لائحة الدعوى المنظمة
# ============================================================
class LawsuitDrafter:
    """مساعد صياغة لائحة الدعوى العمالية."""

    def draft_lawsuit(self, case_data: Dict) -> str:
        today = datetime.now().strftime("%Y-%m-%d")

        facts_list = case_data.get("facts", [])
        facts_text = "\n".join(f"{i}. {f}" for i, f in enumerate(facts_list, 1)) if facts_list else "—"

        claims_list = case_data.get("claims", [])
        claims_text = "\n".join(f"{i}. {c}" for i, c in enumerate(claims_list, 1)) if claims_list else "—"

        evidence_list = case_data.get("evidence", [])
        evidence_text = "\n".join(f"{i}. {e}" for i, e in enumerate(evidence_list, 1)) if evidence_list else "—"

        articles = case_data.get("articles", [])
        articles_text = "، ".join(f"المادة ({a}) من نظام العمل" for a in articles) if articles else "نظام العمل السعودي"

        return f"""
بسم الله الرحمن الرحيم

                        ⚖️ **لائحة دعوى عمالية**

إلى معالي رئيس المحكمة العمالية الموقر                                  التاريخ: {today}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**أولاً: بيانات المدعي**
- الاسم: {case_data.get('plaintiff_name', '____________')}
- رقم الهوية: {case_data.get('plaintiff_id', '____________')}
- الجنسية: {case_data.get('plaintiff_nationality', '____________')}

**ثانياً: بيانات المدعى عليه**
- الاسم (الشركة/المؤسسة): {case_data.get('defendant_name', '____________')}
- السجل التجاري: {case_data.get('defendant_cr', '____________')}

**ثالثاً: البيانات الوظيفية**
- المسمى الوظيفي: {case_data.get('job_title', '____________')}
- تاريخ بداية العمل: {case_data.get('start_date', '____________')}
- تاريخ نهاية العمل: {case_data.get('end_date', '____________')}
- الراتب الأساسي: {case_data.get('basic_salary', 0):,.0f} ريال

**رابعاً: موضوع الدعوى**
{case_data.get('case_type', '____________')}

**خامساً: الوقائع**
{facts_text}

**سادساً: المطالبات**
{claims_text}

**سابعاً: الإسناد القانوني**
تستند هذه الدعوى إلى {articles_text} ولائحته التنفيذية،
وإلى قرارات المحكمة العليا والمبادئ القضائية المستقرة.

**ثامناً: الأدلة المرفقة**
{evidence_text}

**تاسعاً: الطلبات الختامية**
ألتمس من معاليكم:
1. قبول هذه الدعوى شكلاً وموضوعاً.
2. إلزام المدعى عليه بدفع كامل المستحقات المطالب بها.
3. إلزام المدعى عليه بدفع أتعاب المحاماة ومصاريف الدعوى.

وتفضلوا بقبول فائق الاحترام والتقدير،،،

المدعي: {case_data.get('plaintiff_name', '____________')}
التوقيع: ___________________
التاريخ: {today}
"""

# ============================================================
# المثيلات العامة
# ============================================================
evidence_analyzer = EvidenceAnalyzer()
settlement_calculator = SettlementCalculator()
litigation_timeline = LitigationTimeline()
lawsuit_drafter = LawsuitDrafter()
