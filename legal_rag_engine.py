# legal_rag_engine.py
"""
محرك الاسترجاع القانوني الذكي.
يصنف المواد حسب النظام، ويستدعي الأنظمة الستة حسب السياق.
"""
from typing import List, Dict, Any, Optional
import re

class LegalRAGEngine:
    """محرك الاسترجاع القانوني الذكي"""

    def __init__(self, law_db: List[Dict]):
        self.law_db = law_db
        self.categories = {
            "labor": [],
            "evidence": [],
            "electronic": [],
            "procedural": [],
            "other": []
        }
        self._categorize_laws()

    def _categorize_laws(self):
        """تصنيف المواد حسب النظام"""
        labor_keywords = ["عمل", "عامل", "صاحب عمل", "أجور", "راتب", "مكافأة", "فصل", "استقالة"]
        evidence_keywords = ["إثبات", "بينة", "دليل", "شهادة", "إقرار", "محرر"]
        electronic_keywords = ["التعاملات الإلكترونية", "توقيع إلكتروني", "ختم إلكتروني", "بريد إلكتروني"]
        procedural_keywords = ["مرافعات", "محكمة", "دعوى", "اختصاص", "تقادم", "تبليغ"]

        for law in self.law_db:
            text = law.get("text", "").lower()
            law_name = law.get("law_name", "").lower()
            if any(kw in text or kw in law_name for kw in labor_keywords):
                self.categories["labor"].append(law)
            elif any(kw in text or kw in law_name for kw in evidence_keywords):
                self.categories["evidence"].append(law)
            elif any(kw in text or kw in law_name for kw in electronic_keywords):
                self.categories["electronic"].append(law)
            elif any(kw in text or kw in law_name for kw in procedural_keywords):
                self.categories["procedural"].append(law)
            else:
                self.categories["other"].append(law)

    def retrieve(self, query: str, context: str = "all", top_k: int = 7) -> List[Dict]:
        """
        استرجاع المواد القانونية الأكثر صلة بالسؤال.
        context يمكن أن يكون: "labor", "evidence", "electronic", "procedural", "all"
        """
        if context == "all":
            pool = self.law_db
        else:
            pool = self.categories.get(context, self.law_db)

        if not pool:
            return []

        # استخدام بحث بسيط (TF-IDF سيكون في الواجهة الرئيسية)
        # هنا نعيد المواد التي تحتوي على كلمات المفتاح
        keywords = re.findall(r'[\u0600-\u06ff]{3,}', query)
        scored = []
        for idx, law in enumerate(pool):
            text = law.get("text", "").lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, law))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [law for _, law in scored[:top_k]]

    def get_relevant_systems(self, query: str) -> List[str]:
        """تحديد أي الأنظمة الستة يجب استدعاؤها بناءً على السؤال"""
        systems = []
        if any(kw in query for kw in ["فصل", "مكافأة", "راتب", "عمل"]):
            systems.append("نظام العمل")
        if any(kw in query for kw in ["إثبات", "دليل", "بينة", "شهادة"]):
            systems.append("نظام الإثبات")
        if any(kw in query for kw in ["بريد إلكتروني", "توقيع إلكتروني", "مراسلة"]):
            systems.append("نظام التعاملات الإلكترونية")
        if any(kw in query for kw in ["دعوى", "محكمة", "مرافعة", "تقادم"]):
            systems.append("نظام المرافعات الشرعية")
        return systems