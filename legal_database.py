# legal_database.py - Saudi Labor Law Database
# Contains articles, laws, and legal references for Saudi Labor Law

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import streamlit as st

# ======================
# DATABASE STRUCTURE
# ======================

class LegalDatabase:
    """Main class for Saudi Labor Law database operations"""

    def __init__(self):
        self.db_path = Path(__file__).parent / "data" / "saudi_labor_law.json"
        self.articles = self._load_database()

    def _load_database(self) -> Dict:
        """Load the legal database from JSON file or use default data"""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Failed to load database: {e}")

        # Default Saudi Labor Law articles (simplified)
        return {
            "labor_law": {
                "name": "نظام العمل السعودي",
                "last_updated": "2024-01-01",
                "articles": {
                    "1": {
                        "title": "تعريف النظام",
                        "content": "نظام العمل هو النظام الذي ينظم علاقات العمل بين صاحب العمل والعامل.",
                        "category": "تعريفات",
                        "tags": ["تعريف", "نظام", "عمل"],
                        "penalties": [],
                        "related_articles": [2, 3]
                    },
                    "2": {
                        "title": "نطاق التطبيق",
                        "content": "يسري هذا النظام على جميع العمال وصاحب العمل في المملكة العربية السعودية.",
                        "category": "نطاق التطبيق",
                        "tags": ["نطاق", "تطبيق", "جميع"],
                        "penalties": [],
                        "related_articles": [1, 4]
                    },
                    "3": {
                        "title": "استثناءات النظام",
                        "content": "لا يسري هذا النظام على موظفي الدولة والعاملين في المنازل المنزلية.",
                        "category": "استثناءات",
                        "tags": ["استثناء", "منازل", "دولة"],
                        "penalties": [],
                        "related_articles": [1]
                    },
                    "4": {
                        "title": "تعريف العامل",
                        "content": "العامل هو كل شخص طبيعي يعمل تحت إدارة أو إشراف صاحب عمل مقابل أجر.",
                        "category": "تعريفات",
                        "tags": ["عامل", "تعريف", "أجر"],
                        "penalties": [],
                        "related_articles": [2, 5]
                    },
                    "5": {
                        "title": "تعريف صاحب العمل",
                        "content": "صاحب العمل هو كل شخص طبيعي أو اعتباري يستخدم عاملا أو أكثر مقابل أجر.",
                        "category": "تعريفات",
                        "tags": ["صاحب العمل", "تعريف"],
                        "penalties": [],
                        "related_articles": [2, 4]
                    },
                    "40": {
                        "title": "ساعات العمل",
                        "content": "لا يجوز أن تتجاوز ساعات العمل 8 ساعات يوميا أو 48 ساعة أسبوعيا.",
                        "category": "ساعات العمل",
                        "tags": ["ساعات", "عمل", "8 ساعات"],
                        "penalties": ["غرامة مالية", "إغلاق المنشأة"],
                        "related_articles": [41, 42]
                    },
                    "41": {
                        "title": "ساعات العمل في رمضان",
                        "content": "خلال شهر رمضان المبارك، تكون ساعات العمل 6 ساعات يوميا.",
                        "category": "ساعات العمل",
                        "tags": ["رمضان", "6 ساعات"],
                        "penalties": ["غرامة مالية"],
                        "related_articles": [40, 42]
                    },
                    "42": {
                        "title": "فترات الراحة",
                        "content": "يحق للعامل فترة راحة لا تقل عن نصف ساعة بعد 5 ساعات عمل متواصل.",
                        "category": "ساعات العمل",
                        "tags": ["راحة", "30 دقيقة"],
                        "penalties": ["غرامة مالية"],
                        "related_articles": [40, 41]
                    },
                    "50": {
                        "title": "الأجر الأساسي",
                        "content": "يجب دفع الأجر المتفق عليه في الموعد المحدد، ولا يجوز تأخيره أكثر من 7 أيام.",
                        "category": "الأجور",
                        "tags": ["أجر", "دفع", "7 أيام"],
                        "penalties": ["غرامة مالية", "تعويض العامل"],
                        "related_articles": [51, 52]
                    },
                    "51": {
                        "title": "حسم الأجر",
                        "content": "لا يجوز حسم أكثر من 10% من الأجر الأساسي بدون موافقة العامل.",
                        "category": "الأجور",
                        "tags": ["حسم", "10%", "موافقة"],
                        "penalties": ["غرامة مالية", "إلغاء الحسم"],
                        "related_articles": [50, 52]
                    },
                    "52": {
                        "title": "علاوة نهاية الخدمة",
                        "content": "يستحق العامل علاوة نهاية الخدمة بعد عامين من العمل المتواصل.",
                        "category": "مكافآت",
                        "tags": ["علاوة", "نهاية الخدمة", "عامين"],
                        "penalties": ["تعويض العامل"],
                        "related_articles": [50, 51]
                    },
                    "60": {
                        "title": "إنهاء عقد العمل",
                        "content": "يجوز لأي من الطرفين إنهاء عقد العمل قبل انتهاء مدته إذا لم يكن هناك اتفاق على خلاف ذلك.",
                        "category": "إنهاء العقد",
                        "tags": ["إنهاء", "عقد", "إخطار"],
                        "penalties": ["تعويض"],
                        "related_articles": [61, 62]
                    },
                    "61": {
                        "title": "إخطار إنهاء العقد",
                        "content": "يجب إبلاغ الطرف الآخر بكتابة قبل 30 يوما من تاريخ إنهاء العقد.",
                        "category": "إنهاء العقد",
                        "tags": ["إخطار", "30 يوم", "كتابة"],
                        "penalties": ["تعويض عن عدم الإخطار"],
                        "related_articles": [60, 62]
                    },
                    "62": {
                        "title": "تعويض إنهاء العقد",
                        "content": "إذا لم يتم إبلاغ العامل بكتابة، يستحق تعويضا عن فترة الإخطار.",
                        "category": "إنهاء العقد",
                        "tags": ["تعويض", "إخطار", "كتابة"],
                        "penalties": [],
                        "related_articles": [60, 61]
                    },
                    "70": {
                        "title": "إجازات سنوية",
                        "content": "يستحق العامل إجازة سنوية مدفوعة الأجر لمدة 21 يوما بعد عام من العمل.",
                        "category": "إجازات",
                        "tags": ["إجازة", "21 يوم", "مدفوعة"],
                        "penalties": ["تعويض عن الإجازة"],
                        "related_articles": [71, 72]
                    },
                    "71": {
                        "title": "إجازات مرضية",
                        "content": "يستحق العامل إجازة مرضية مدفوعة الأجر لمدة 30 يوما في السنة.",
                        "category": "إجازات",
                        "tags": ["مرضية", "30 يوم", "مدفوعة"],
                        "penalties": [],
                        "related_articles": [70, 72]
                    },
                    "72": {
                        "title": "إجازات بدون راتب",
                        "content": "يمكن منح العامل إجازة بدون راتب لمدة لا تتجاوز 4 أشهر في السنة.",
                        "category": "إجازات",
                        "tags": ["بدون راتب", "4 أشهر"],
                        "penalties": [],
                        "related_articles": [70, 71]
                    },
                    "80": {
                        "title": "سلامة العمل",
                        "content": "يجب على صاحب العمل توفير بيئة عمل آمنة وخالية من المخاطر.",
                        "category": "سلامة العمل",
                        "tags": ["سلامة", "آمنة", "مخاطر"],
                        "penalties": ["غرامة مالية", "إغلاق المنشأة"],
                        "related_articles": [81, 82]
                    },
                    "81": {
                        "title": "معدات السلامة",
                        "content": "يجب توفير معدات السلامة اللازمة حسب طبيعة العمل.",
                        "category": "سلامة العمل",
                        "tags": ["معدات", "سلامة", "ضرورية"],
                        "penalties": ["غرامة مالية"],
                        "related_articles": [80, 82]
                    },
                    "82": {
                        "title": "تدريب السلامة",
                        "content": "يجب تدريب العمال على إجراءات السلامة ومخاطر العمل.",
                        "category": "سلامة العمل",
                        "tags": ["تدريب", "إجراءات", "مخاطر"],
                        "penalties": ["غرامة مالية"],
                        "related_articles": [80, 81]
                    },
                    "90": {
                        "title": "تمييز العامل",
                        "content": "يحرم التمييز بين العمال بناءً على الجنس أو الدين أو الجنسية.",
                        "category": "حقوق العامل",
                        "tags": ["تمييز", "محرم", "حقوق"],
                        "penalties": ["غرامة مالية", "تعويض"],
                        "related_articles": [91, 92]
                    },
                    "91": {
                        "title": "حقوق المرأة العاملة",
                        "content": "للمرأة العاملة نفس حقوق الرجل في العمل والأجر.",
                        "category": "حقوق العامل",
                        "tags": ["مرأة", "حقوق", "مساواة"],
                        "penalties": ["تمييز", "غرامة"],
                        "related_articles": [90, 92]
                    },
                    "92": {
                        "title": "حقوق العمال الأجانب",
                        "content": "للعمال الأجانب نفس حقوق العمال السعوديين حسب النظام.",
                        "category": "حقوق العامل",
                        "tags": ["أجانب", "حقوق", "مساواة"],
                        "penalties": ["تمييز", "غرامة"],
                        "related_articles": [90, 91]
                    }
                }
            },
            "penalty_codes": {
                "غرامة مالية": {
                    "description": "غرامة مالية تتراوح بين 5000 و 10000 ريال",
                    "legal_basis": "المادة 10 من نظام العمل"
                },
                "إغلاق المنشأة": {
                    "description": "إغلاق المنشأة لمدة لا تتجاوز 30 يوما",
                    "legal_basis": "المادة 11 من نظام العمل"
                },
                "تعويض العامل": {
                    "description": "تعويض العامل عن الأضرار التي لحقت به",
                    "legal_basis": "المادة 12 من نظام العمل"
                },
                "تعويض عن عدم الإخطار": {
                    "description": "تعويض عن عدم إبلاغ العامل بكتابة قبل إنهاء العقد",
                    "legal_basis": "المادة 61 من نظام العمل"
                },
                "تعويض عن الإجازة": {
                    "description": "تعويض عن عدم منح العامل إجازته السنوية",
                    "legal_basis": "المادة 70 من نظام العمل"
                }
            }
        }

    def get_article(self, article_id: str) -> Optional[Dict]:
        """Get a specific article by its ID"""
        try:
            return self.articles["labor_law"]["articles"].get(article_id)
        except (KeyError, AttributeError):
            return None

    def search_articles(self, query: str, limit: int = 10) -> List[Dict]:
        """Search articles by content, title, or tags"""
        results = []
        query_lower = query.lower()

        for article_id, article in self.articles["labor_law"]["articles"].items():
            if (query_lower in article["title"].lower() or
                query_lower in article["content"].lower() or
                any(query_lower in tag.lower() for tag in article["tags"])):
                results.append({
                    "id": article_id,
                    "title": article["title"],
                    "content": article["content"],
                    "category": article["category"],
                    "tags": article["tags"],
                    "score": self._calculate_score(article, query_lower)
                })

        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _calculate_score(self, article: Dict, query: str) -> float:
        """Calculate relevance score for search results"""
        score = 0

        # Exact match in title
        if query in article["title"].lower():
            score += 10

        # Exact match in content
        if query in article["content"].lower():
            score += 5

        # Match in tags
        for tag in article["tags"]:
            if query in tag.lower():
                score += 3

        # Partial match
        if any(word in article["title"].lower() for word in query.split()):
            score += 2
        if any(word in article["content"].lower() for word in query.split()):
            score += 1

        return score

    def get_articles_by_category(self, category: str) -> List[Dict]:
        """Get all articles in a specific category"""
        return [
            {"id": aid, **data}
            for aid, data in self.articles["labor_law"]["articles"].items()
            if data["category"] == category
        ]

    def get_all_categories(self) -> List[str]:
        """Get list of all unique categories"""
        return list(set(
            article["category"]
            for article in self.articles["labor_law"]["articles"].values()
        ))

    def get_penalty_info(self, penalty_type: str) -> Optional[Dict]:
        """Get information about a specific penalty type"""
        return self.articles["penalty_codes"].get(penalty_type)

    def get_related_articles(self, article_id: str) -> List[Dict]:
        """Get articles related to a specific article"""
        article = self.get_article(article_id)
        if not article or not article.get("related_articles"):
            return []

        related_ids = article["related_articles"]
        return [
            {"id": rid, **self.articles["labor_law"]["articles"][rid]}
            for rid in related_ids
            if rid in self.articles["labor_law"]["articles"]
        ]

    def save_database(self, path: Optional[str] = None) -> bool:
        """Save the database to a JSON file"""
        try:
            save_path = Path(path) if path else self.db_path
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.articles, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Failed to save database: {e}")
            return False

    def add_article(self, article_data: Dict) -> bool:
        """Add a new article to the database"""
        try:
            article_id = str(len(self.articles["labor_law"]["articles"]) + 1)
            self.articles["labor_law"]["articles"][article_id] = article_data
            return self.save_database()
        except Exception as e:
            st.error(f"Failed to add article: {e}")
            return False

# ======================
# GLOBAL INSTANCE
# ======================

# Create a single instance of the database
_legal_db = LegalDatabase()

def get_legal_database() -> LegalDatabase:
    """Get the global legal database instance"""
    return _legal_db

# For backward compatibility
legal_database = _legal_db
