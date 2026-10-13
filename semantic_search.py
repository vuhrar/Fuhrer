# semantic_search.py
"""
محرك البحث القانوني — المرحلة 1.

يستبدل هذا الملف العدّ الحرفي لتكرار الكلمات (الذي كان في legal_tools_advanced.py
القديم) بترتيب فعلي بالأهمية الإحصائية للكلمات عبر TF-IDF + تشابه جيب التمام،
باستخدام scikit-learn المتوفر محليًا فعلاً (تحققت: مثبتة في requirements.txt
ومتوفرة في بيئة التشغيل).

⚠️ حد صادق يجب معرفته: TF-IDF ليس بحثًا دلاليًا بالمعنى الكامل — يرتّب حسب
الكلمات الفعلية المشتركة ووزنها الإحصائي، لكنه لا "يفهم" أن "فصل تعسفي" و"إنهاء
غير مشروع" يتحدثان عن نفس المسألة إن لم تشتركا في جذر كلمة. هذا تحسّن حقيقي
وجوهري عن العدّ الحرفي القديم (ترتيب بالأهمية لا بالتكرار الخام، مطابقة جزئية
لجذور الكلمات عبر n-grams حرفية)، وليس بديلاً كاملاً للتضمينات.

مسار الترقية إلى تضمينات حقيقية (EmbeddingSearchIndex أدناه) مكتوب وجاهز
بواجهة قياسية لمكتبة sentence-transformers، **لكن غير مُختبر في هذه البيئة**:
هذه البيئة الحاوية بلا اتصال شبكة، ولا يمكنها تحميل أوزان أي نموذج تضمين من
HuggingFace. بيئة نشرك الفعلية (خادمك الذي يشغّل uvicorn) لديها على الأرجح
اتصال إنترنت عاديًا؛ إن ثبّتّ sentence-transformers هناك سيُستخدم تلقائيًا
(get_search_index يكتشف توفرها ويستخدمها، وإلا يسقط تلقائيًا إلى TF-IDF دون
أي كسر). لا تُصدّق أن هذا المسار "يعمل" حتى تُشغّله فعليًا وتراجع نتائجه.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _kb_json_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "law_knowledge_base.json")


def build_corpus() -> List[Dict[str, Any]]:
    """
    يوحّد مصدرين بمستويي ثقة مختلفين صراحة، لا يخلطهما دون تمييز:
    - curated: ~25 مادة من legal_database.py مُدخلة يدويًا ومُراجَعة — أعلى ثقة.
    - extracted: مواد law_knowledge_base.json المستخرجة آليًا من law_text.txt
      بعد تنظيف NFKC — ثقة جيدة لكن معلَّمة فرديًا (needs_verification) حيث
      وُجد تشويه متبقٍ لم يُصلَح آليًا عمدًا.
    """
    from legal_database import get_legal_database

    docs: List[Dict[str, Any]] = []
    # ← إصلاح: get_all_articles() القديمة كانت تُستخدم هنا، لكنها تُعيد
    # المواد المنسّقة والمستخرجة مدموجة معًا (legal_database.__init__ يدمجها
    # أصلًا)، فكانت كل مادة مستخرجة تُصنَّف "curated" هنا مرة، ثم تتكرر
    # "extracted" مرة أخرى أدناه — تكرار ومستوى ثقة خاطئ معًا.
    # get_curated_articles() الجديدة تُعيد فقط الـ25 المُدخلة يدويًا فعلًا.
    database = get_legal_database()
    official_active = getattr(database, "_source_mode", "") == "official_snapshot"
    for art in database.get_curated_articles():
        docs.append({
            "doc_id": f"curated_{art.get('article')}",
            "article": art.get("article"),
            "title": art.get("title", ""),
            "category": art.get("category", ""),
            "text": art.get("text", ""),
            "trust_tier": "official_snapshot" if official_active else "curated",
            "needs_verification": False,
            "source_id": art.get("source_id", "boe_labor_law" if official_active else "manual_curated"),
            "source_status": art.get("source_status", "ساري" if official_active else "يتطلب تحققًا من المصدر الرسمي"),
        })

    kb_path = _kb_json_path()
    if os.path.exists(kb_path) and not official_active:
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                systems = json.load(f)
            for system in systems:
                sys_name = system.get("system", "نظام عام")
                for art in system.get("articles", []):
                    text = art.get("text", "")
                    if not _is_labor_relevant(text):
                        continue  # استبعاد مواد من أنظمة لا علاقة لها بالعمل (تصديق رقمي، أدوية مخدرة...)
                    docs.append({
                        "doc_id": f"extracted_{sys_name}_{art.get('id')}",
                        "article": str(art.get("article_number") or art.get("id", "")),
                        "title": art.get("id", "مادة"),
                        "category": sys_name,
                        "text": text,
                        "trust_tier": "extracted",
                        "needs_verification": art.get("needs_verification", False),
                        "system_title_confidence": system.get("title_confidence"),
                    })
        except Exception:
            pass  # لا نُسقط كامل البحث إن تعذّرت قراءة الملف الموسّع؛ نكتفي بالمُنسَّق يدويًا
    return [d for d in docs if (d["text"] or "").strip()]


_LABOR_KEYWORDS = ["عامل", "العمل", "صاحب العمل", "الأجر", "أجره", "الخدمة", "إجازة", "عقد العمل", "إصابة عمل", "فصل", "إنهاء الخدمة", "ساعات العمل", "التأمينات الاجتماعية", "مكافأة", "إشعار"]


def _is_labor_relevant(text: str) -> bool:
    """
    فلتر صلة بسيط: على الأقل كلمتان مفتاحيتان متمايزتان من مفردات نظام
    العمل. حدود الأنظمة في law_text.txt غير موثوقة (المرحلة 1)، فهذا الفلتر
    يعتمد على محتوى النص نفسه لا على اسم "النظام" المُستنتَج، ويستبعد مواد
    من أنظمة أخرى تمامًا (تعاملات إلكترونية، تصديق رقمي، أدوية مخدرة...)
    انتهت بالخطأ في نفس المتن الخام بسبب حدود الأنظمة غير الموثوقة.
    """
    hits = sum(1 for kw in _LABOR_KEYWORDS if kw in text)
    return hits >= 2


class TfidfSearchIndex:
    """فهرسة TF-IDF فعلية — تعمل الآن، بلا اعتماد على شبكة أو نموذج خارجي."""

    def __init__(self, corpus: Optional[List[Dict[str, Any]]] = None):
        self.corpus = corpus if corpus is not None else build_corpus()
        texts = [d["text"] for d in self.corpus]
        # analyzer بمستوى الحروف (char n-grams) يمنح تسامحًا جزئيًا مع اختلاف
        # صيغ الكلمة العربية (جذر/تصريف) أكثر من مطابقة الكلمة الكاملة فقط.
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
        self.matrix = self.vectorizer.fit_transform(texts) if texts else None

    def search(self, query: str, category: Optional[str] = None, max_results: int = 10, min_score: float = 0.1) -> List[Dict[str, Any]]:
        if not query or self.matrix is None:
            return []
        candidates = self.corpus
        matrix = self.matrix
        if category:
            idx = [i for i, d in enumerate(self.corpus) if d["category"] == category]
            if not idx:
                return []
            candidates = [self.corpus[i] for i in idx]
            matrix = self.matrix[idx]
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, matrix).flatten()
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        results, seen_text = [], set()
        for doc, score in ranked:
            if score < min_score or len(results) >= max_results:
                break
            # المصدران (المنسّق والمستخرج) يتداخلان فعليًا على نفس مواد نظام
            # العمل؛ نُبقي الأعلى ثقة فقط عند تطابق النص لتفادي عرض نفس
            # المادة مرتين في نتائج البحث.
            key = " ".join((doc["text"] or "")[:200].split())
            if key in seen_text:
                continue
            seen_text.add(key)
            results.append({**{k: v for k, v in doc.items() if k != "doc_id"}, "score": round(float(score), 4), "search_method": "tfidf_char_ngram"})
        return results


class EmbeddingSearchIndex:
    """
    مسار الترقية إلى بحث دلالي حقيقي بالتضمينات — مكتوب بواجهة قياسية،
    **غير مُختبر هنا** (لا شبكة في هذه الحاوية لتحميل النموذج). سيُستخدم
    تلقائيًا فقط إن نجح التحميل الفعلي؛ أي استثناء يسقط تلقائيًا إلى TF-IDF.
    """

    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, corpus: Optional[List[Dict[str, Any]]] = None):
        from sentence_transformers import SentenceTransformer  # قد يرمي ImportError عمدًا هنا

        self.corpus = corpus if corpus is not None else build_corpus()
        self.model = SentenceTransformer(self.MODEL_NAME)
        texts = [d["text"] for d in self.corpus]
        self.embeddings = self.model.encode(texts, normalize_embeddings=True) if texts else None

    def search(self, query: str, category: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        if not query or self.embeddings is None:
            return []
        candidates, embeddings = self.corpus, self.embeddings
        if category:
            idx = [i for i, d in enumerate(self.corpus) if d["category"] == category]
            if not idx:
                return []
            candidates = [self.corpus[i] for i in idx]
            embeddings = self.embeddings[idx]
        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        scores = embeddings @ q_emb
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        results = []
        for doc, score in ranked[:max_results]:
            if score <= 0:
                continue
            results.append({**{k: v for k, v in doc.items() if k != "doc_id"}, "score": round(float(score), 4), "search_method": "embeddings_minilm"})
        return results


_INDEX = None


def get_search_index():
    """يحاول التضمينات الحقيقية أولًا؛ أي فشل (غالبًا: لا مكتبة أو لا شبكة) يسقط تلقائيًا وبصمت لـ TF-IDF الفعّال محليًا."""
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    corpus = build_corpus()
    try:
        _INDEX = EmbeddingSearchIndex(corpus)
    except Exception:
        _INDEX = TfidfSearchIndex(corpus)
    return _INDEX
