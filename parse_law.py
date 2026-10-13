# parse_law.py
"""
← أُعيد بناؤه بالكامل في المرحلة 1. مشكلتان حقيقيتان في النسخة القديمة:

1. كانت تعمل مباشرة على النص الخام المشوّه (أشكال عرض يونيكود غير مُطبَّعة)
   دون أي تنظيف، فتُنتج قاعدة معرفة بحروف عربية مقلوبة الشكل بالكامل.
   الآن: تمر كل النصوص أولًا عبر law_corpus_tools.clean_text (تطبيع NFKC
   حتمي وآمن، ليس تخمينًا) قبل أي تحليل.

2. نمط المواد regex القديم يسرد الأعداد الترتيبية يدويًا وكان يتوقف عند
   "المائة" — أي 100 فقط. هذا الملف يحتوي فعليًا مواد بعد المائة (تحقّقتُ:
   "المادة الخامسة والستون بعد المائة" = 165 موجودة فعليًا في النص)، وأي
   نظام سعودي متوسط الحجم يتجاوز غالبًا 100 مادة. الصيغة القديمة كانت تفقد
   هذه المواد بصمت دون أي خطأ أو تحذير. الآن: law_corpus_tools.parse_arabic_ordinal
   يفهم صيغة "X بعد المائة/المائتين" ويحوّلها لرقم صحيح حقيقي.

كل مادة الآن تحمل أيضًا article_number (رقم صحيح أو None إن تعذّر الفهم)
وneeds_verification (True إن احتوى نصها موضعًا مشبوهًا لم يُصلحه NFKC —
راجع law_corpus_tools.py لتفاصيل لماذا لم يُصلَح تلقائيًا).
"""
import json
import os
import re

from law_corpus_tools import clean_text, extract_articles


def _flag_title_confidence(systems: list) -> list:
    """
    ← محاولة أولى كانت تدمج تلقائيًا الأقسام التي لا تبدأ مادتها الأولى من
    (1)، لكن الاختبار الفعلي على النص الكامل أظهر أن هذا يدمج أنظمة مختلفة
    فعليًا (مثل نظام التعاملات الإلكترونية) في كتلة واحدة خاطئة — أي أن
    الدمج التلقائي كان "صوريًا" هو الآخر: يبدو منظّمًا لكنه غير موثوق. تم
    التراجع عنه عمدًا. البديل الأكثر أمانة: لا حذف ولا دمج لأي بيانات؛
    فقط تعليم صريح لعناوين الأنظمة غير المؤكدة كي لا تُعرض وكأنها موثوقة
    بنفس درجة عنوان بدأ ترقيمه من المادة الأولى فعلًا. حدود الأنظمة
    الحقيقية في هذا الملف المُسطَّح تحتاج تحققًا يدويًا أو ملفات PDF أصلية
    بحدود صفحات واضحة — لا حلًا آليًا كاملًا بالثقة المطلوبة لنص نظامي.
    """
    for system in systems:
        first_numbers = [a["article_number"] for a in system["articles"] if a["article_number"] is not None]
        confident = bool(first_numbers) and first_numbers[0] <= 3
        system["title_confidence"] = "مرتفعة" if confident else "منخفضة — قد يكون هذا العنوان جزءًا من نظام سابق لا عنوانًا حقيقيًا، تحقق يدويًا"
    return systems


def parse_law_text(file_path: str) -> list:
    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()
    content = clean_text(raw)

    # تقسيم المحتوى إلى أنظمة — الأنظمة تبدأ غالبًا بـ"تنظيم" أو "نظام" أو "ضوابط"
    raw_sections = re.split(r"\n(?=ضوابط|تنظيم|نظام)\s*", content)

    systems = []
    for section in raw_sections:
        lines = section.strip().split("\n")
        if not lines or not lines[0].strip():
            continue
        system_name = lines[0].strip()
        body = "\n".join(lines[1:])
        articles = extract_articles(body)
        if articles:
            systems.append({"system": system_name, "articles": articles})
    return _flag_title_confidence(systems)


if __name__ == "__main__":
    input_file = "law_text.txt"
    output_file = "law_knowledge_base.json"

    if os.path.exists(input_file):
        data = parse_law_text(input_file)
        total_articles = sum(len(s["articles"]) for s in data)
        flagged = sum(1 for s in data for a in s["articles"] if a["needs_verification"])
        numbered = sum(1 for s in data for a in s["articles"] if a["article_number"] is not None)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"تم تحليل {len(data)} نظامًا و{total_articles} مادة إلى {output_file}")
        print(f"مواد بها رقم مفهوم آليًا: {numbered}/{total_articles}")
        print(f"مواد تحتاج تحقق يدوي (تشويه متبقٍ): {flagged}/{total_articles}")
    else:
        print(f"لم يُعثر على ملف الإدخال: {input_file}")
