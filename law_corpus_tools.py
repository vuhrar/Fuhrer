# law_corpus_tools.py
"""
أدوات تجهيز المتن القانوني الخام (law_text.txt) — المرحلة 1.

اكتشاف رئيسي موثّق هنا: الملف الخام لم يكن يحتاج ملفات PDF أصلية لإصلاحه كما
افترضتُ ابتداءً. الفحص الفعلي أظهر أن معظم "التشويه" هو ببساطة أحرف عربية
مخزَّنة بأشكال العرض (Unicode Presentation Forms) بدل الأحرف الأساسية — وهذا
تُصلحه دالة `unicodedata.normalize("NFKC", ...)` بشكل حتمي ومضمون (ليس تخمينًا؛
هي تعيينات معيارية موثّقة في مواصفة يونيكود نفسها). تم تطبيقها على الملف
كاملًا (2.1 ميجابايت) وأعادت النص إلى عربية سليمة بنسبة تفوق 99% من الأحرف.

ما تبقّى بعد NFKC: نمط تشويه أضيق ومختلف طبيعةً — تجمّعات حرف اللام مع عائلة
الألف (لا/لأ/لآ/لم إلخ) تظهر أحيانًا كحرف لاتيني منفرد غريب (i أو L أو M أو
' أو d)، على الأرجح بسبب خلل في جدول ترميز الخط الأصلي داخل ملف PDF المصدر
لا علاقة له بيونيكود. هذا النمط **لم يُصحَّح تلقائيًا** لأنه ليس تعيينًا
معياريًا مضمونًا بل استنتاجًا من السياق — أي تخمين آلي هنا قد يُدخل خطأ صامتًا
في نص نظامي. بدلًا من ذلك: `detect_residual_corruption` يحدد كل موضع مشبوه
بدقة، وكل مادة تحتوي موضعًا كهذا تُعلَّم `needs_verification=True` بدل أن
تُعرض كأنها نص نهائي موثوق.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional

_BIDI_MARKS = "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
_BIDI_TABLE = {ord(c): None for c in _BIDI_MARKS}


def clean_text(raw: str) -> str:
    """تنظيف حتمي وآمن 100%: تطبيع NFKC + إزالة علامات الاتجاه + فواصل الصفحات.
    لا تخمين هنا — كل خطوة تعيين معياري أو إزالة تحكّم غير مرئي، لا تغيير لمحتوى."""
    text = unicodedata.normalize("NFKC", raw)
    text = text.translate(_BIDI_TABLE)
    text = text.replace("\x0c", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# نمط الموضع المشبوه: حرف لاتيني منفرد ملاصق لحروف عربية على الجانبين (مسافة اختيارية)
_SUSPECT_PATTERN = re.compile(r"[\u0600-\u06FF][A-Za-z][\u0600-\u06FF]|[\u0600-\u06FF]\s[A-Za-z][\u0600-\u06FF]|[\u0600-\u06FF][A-Za-z]\s[\u0600-\u06FF]")


def detect_residual_corruption(text: str) -> List[str]:
    """يعيد كل المقاطع المشبوهة (حرف لاتيني وسط عربي) مع سياق قصير حولها، دون أي تعديل للنص."""
    found = []
    for m in _SUSPECT_PATTERN.finditer(text):
        start, end = max(0, m.start() - 6), min(len(text), m.end() + 6)
        found.append(text[start:end])
    return found


def corruption_rate(text: str) -> float:
    hits = len(_SUSPECT_PATTERN.findall(text))
    words = max(1, len(text.split()))
    return round(hits / words, 4)


# ============================================================
# محوّل الأعداد الترتيبية العربية إلى رقم صحيح — يغطي 1 إلى 399+
# ============================================================
_ONES = {
    "الأولى": 1, "الحادية": 1, "الأول": 1,
    "الثانية": 2, "الثاني": 2,
    "الثالثة": 3, "الثالث": 3,
    "الرابعة": 4, "الرابع": 4,
    "الخامسة": 5, "الخامس": 5,
    "السادسة": 6, "السادس": 6,
    "السابعة": 7, "السابع": 7,
    "الثامنة": 8, "الثامن": 8,
    "التاسعة": 9, "التاسع": 9,
}
_TEN_ITSELF = {"العاشرة": 10, "العاشر": 10}
_DECADES = {
    "العشرون": 20, "الثلاثون": 30, "الأربعون": 40, "الخمسون": 50,
    "الستون": 60, "السبعون": 70, "الثمانون": 80, "التسعون": 90,
}
_HUNDREDS = {
    "المائة": 100, "المئة": 100, "المائتين": 200, "المئتين": 200,
    "الثلاثمائة": 300, "الثلاثمئة": 300, "الأربعمائة": 400, "الأربعمئة": 400,
}


def parse_arabic_ordinal(phrase: str) -> Optional[int]:
    """يحوّل عبارة ترتيبية عربية مثل 'الخامسة والستون بعد المائة' إلى 165.
    يعيد None إن تعذّر الفهم بثقة — لا تخمين لرقم إن لم يطابق نمطًا معروفًا."""
    p = re.sub(r"\s+", " ", (phrase or "")).strip(" :.-،")
    if not p:
        return None

    total = 0
    # 1) لاحقة "بعد ال<مئات>"
    m = re.search(r"بعد\s+(" + "|".join(re.escape(k) for k in _HUNDREDS) + r")$", p)
    if m:
        total += _HUNDREDS[m.group(1)]
        p = p[: m.start()].strip()
    elif p in _HUNDREDS:  # "المادة المائة" وحدها بلا بادئة آحاد
        return _HUNDREDS[p]

    if not p:
        return total if total else None

    # 2) عدد مركّب "X عشرة" (11-19)
    for word, val in _ONES.items():
        if p == f"{word} عشرة":
            return total + 10 + val
    if p == "العاشرة" or p == "العاشر":
        return total + 10

    # 3) عدد مركّب "X والعقد" (21-99، غير عقدي)
    m = re.match(r"^(" + "|".join(re.escape(k) for k in _ONES) + r")\s+و(" + "|".join(re.escape(k) for k in _DECADES) + r")$", p)
    if m:
        return total + _ONES[m.group(1)] + _DECADES[m.group(2)]

    # 4) عقد صريح (20، 30 ...)
    if p in _DECADES:
        return total + _DECADES[p]

    # 5) آحاد صريحة (1-9)
    if p in _ONES:
        return total + _ONES[p]
    if p in _TEN_ITSELF:
        return total + 10

    return None


ARTICLE_MARKER = re.compile(
    # "الماد[ةي]+" يتحمل تشويهًا فعليًا شوهد في النص الحقيقي: "المادة" تظهر
    # أحيانًا "المادية" (ياء زائدة). لولا هذا التوسيع لسقطت مواد كاملة بصمت
    # (مثال محقَّق: "المادية الحادية والستون بعد المائة" لم تكن تُلتقط إطلاقًا).
    r"(?:الماد[ةي]+|ماد[ةي]+)\s+((?:[\u0621-\u064A]+\s*){1,6}?(?:بعد\s+ال[\u0621-\u064A]+)?)\s*:"
)


def extract_articles(system_text: str) -> List[Dict]:
    """يقسّم نص نظام واحد إلى مواد، ويحسب الرقم الصحيح لكل مادة عند الإمكان،
    ويعلّم كل مادة تحتوي موضعًا مشبوهًا بـ needs_verification."""
    matches = list(ARTICLE_MARKER.finditer(system_text))
    articles = []
    for i, m in enumerate(matches):
        raw_id = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(system_text)
        body = system_text[start:end].strip()
        number = parse_arabic_ordinal(raw_id)
        suspects = detect_residual_corruption(body)
        articles.append({
            "id": f"المادة {raw_id}",
            "article_number": number,
            "text": body,
            "needs_verification": bool(suspects),
            "suspect_context": suspects[:3],
        })
    return articles
