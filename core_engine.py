# core_engine.py
"""
المحرك المركزي - ينسق جميع المحللات ويُنتج تحليلاً استراتيجياً متكاملاً.
"""
from typing import Dict, Any, List, Optional
from advanced_extractor import AdvancedExtractor
from deep_analyzer import DeepAnalyzer
from procedural_analyzer import ProceduralAnalyzer
from discrepancy_analyzer import DiscrepancyAnalyzer
from response_generator import ResponseGenerator
from rules_engine import apply_rules

class CoreEngine:
    """
    المحرك المركزي - يشغل جميع المحللات في تسلسل ذكي.
    """
    def __init__(self):
        self.extractor = AdvancedExtractor()
        self.deep_analyzer = DeepAnalyzer()
        self.procedural_analyzer = ProceduralAnalyzer()
        self.discrepancy_analyzer = DiscrepancyAnalyzer()
        self.response_generator = ResponseGenerator()

    def full_analysis(self, text: str) -> Dict[str, Any]:
        """
        يقوم بتحليل شامل للنص ويعيد جميع المخرجات في هيكل واحد.
        """
        # 1. الاستخراج العميق
        extracted_data = self.extractor.extract(text)

        # 2. التحليل الإداري
        procedural_result = self.procedural_analyzer.analyze(text, extracted_data)

        # 3. تحليل التناقضات
        discrepancy_result = self.discrepancy_analyzer.analyze_documents([{"text": text, "source": "النص"}])

        # 4. التحليل العميق (السببى، النبرة، الموقف)
        deep_result = self.deep_analyzer.analyze(text, extracted_data)

        # 5. تطبيق القواعد
        rules_context = self._prepare_rules_context(extracted_data, procedural_result)
        rules_alerts = apply_rules(rules_context)

        # 6. توليد الحجج المضادة (إن وجد خصم)
        counter_arguments = []
        if extracted_data.get("procedural", {}).get("has_termination_letter"):
            counter_arguments = self.response_generator.generate_counter_arguments(
                opponent_claim="ادعاء الخصم بالفصل", 
                evidence=extracted_data.get("evidence", ["لا يوجد"]),
                extracted_data=extracted_data
            )

        # 7. توليد التوصيات الاستراتيجية
        strategic_recommendations = self._generate_strategic_recommendations(
            extracted_data, procedural_result, deep_result, rules_alerts
        )

        return {
            "extracted_data": extracted_data,
            "procedural_result": procedural_result,
            "discrepancy_result": discrepancy_result,
            "deep_result": deep_result,
            "rules_alerts": rules_alerts,
            "counter_arguments": counter_arguments,
            "strategic_recommendations": strategic_recommendations,
            "full_text": text
        }

    def _prepare_rules_context(self, extracted_data: Dict, procedural_result: Dict) -> Dict:
        """
        يُعد سياق القواعد من البيانات المستخرجة.
        """
        return {
            "days_abandoned": extracted_data.get("employment", {}).get("absence_days", 0),
            "days_since_firing": extracted_data.get("employment", {}).get("days_since_termination", 0),
            "service_length": extracted_data.get("employment", {}).get("service_years", 0),
            "no_investigation": not procedural_result.get("has_investigation", False),
            "arbitrary_dismissal": procedural_result.get("is_arbitrary", False),
            "salary_delay": extracted_data.get("financial", {}).get("salary_delay_months", 0) > 0,
            "eosb_not_paid": extracted_data.get("financial", {}).get("eosb_claimed", 0) == 0,
            "absence_days": extracted_data.get("employment", {}).get("absence_days", 0),
            "settlement_offer": extracted_data.get("procedural", {}).get("has_settlement_offer", False),
            "force_majeure": extracted_data.get("procedural", {}).get("force_majeure", False),
            "proven_illness": extracted_data.get("procedural", {}).get("proven_illness", False)
        }

    def _generate_strategic_recommendations(self, extracted_data: Dict, procedural_result: Dict, 
                                            deep_result: Dict, rules_alerts: List) -> Dict:
        """
        يُولّد توصيات استراتيجية بناءً على جميع التحليلات.
        """
        recommendations = {
            "immediate_actions": [],
            "legal_path": "صلح",
            "strength_score": 0,
            "risk_level": "متوسطة"
        }

        # حساب درجة القوة
        strength = 50  # البداية من 50
        if procedural_result.get("is_arbitrary"):
            strength += 15
        if not procedural_result.get("has_investigation"):
            strength += 10
        if extracted_data.get("financial", {}).get("total_salary", 0) > 10000:
            strength += 5
        if len(extracted_data.get("legal", {}).get("mentioned_articles", [])) > 2:
            strength += 10
        if deep_result.get("tone_analysis", {}).get("acknowledgments_detected", False):
            strength += 10
        # خصم النقاط
        if deep_result.get("tone_analysis", {}).get("threats_detected", False):
            strength -= 5
        if not extracted_data.get("evidence"):
            strength -= 10
        recommendations["strength_score"] = min(100, max(0, strength))

        # تحديد المخاطر
        risk = "منخفضة"
        if extracted_data.get("employment", {}).get("service_years", 0) < 2:
            risk = "مرتفعة"
        elif not extracted_data.get("evidence"):
            risk = "متوسطة"
        if extracted_data.get("legal", {}).get("statute_risk", False):
            risk = "مرتفعة"
        recommendations["risk_level"] = risk

        # التوصيات الإجرائية الفورية
        if not procedural_result.get("has_termination_letter"):
            recommendations["immediate_actions"].append("طلب خطاب فصل رسمي")
        if not procedural_result.get("has_investigation") and procedural_result.get("has_termination_letter"):
            recommendations["immediate_actions"].append("تقديم اعتراض لمكتب العمل")
        if extracted_data.get("financial", {}).get("eosb_claimed", 0) == 0:
            recommendations["immediate_actions"].append("مطالبة بمكافأة نهاية الخدمة")

        # تحديد المسار القانوني الأمثل
        if recommendations["strength_score"] > 70:
            recommendations["legal_path"] = "تقاضي"
        elif recommendations["strength_score"] > 50:
            recommendations["legal_path"] = "إنذار ثم تقاضي"
        else:
            recommendations["legal_path"] = "صلح"

        return recommendations