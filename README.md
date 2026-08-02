# Führar - النظام القانوني الذكي للقانون العمالي السعودي (CLI)

**Führar** هو تطبيق تحليلي قانوني متقدم موجه لمعالجة قضايا القانون العمالي السعودي. تم تعديل المشروع ليكون قابلًا للتشغيل محليًا عبر واجهة سطر الأوامر (CLI) ودون اعتماد على Streamlit.

ميزات النسخة الحالية:
- معالجة مستندات PDF/DOCX/TXT/JSON/CSV/صور (OCR)
- محرك ذكاء اصطناعي هجيني: محاولة استخدام نموذج محلي أولًا (إن وُجد) ثم الرجوع إلى مزود سحابي وفقًا للإعدادات
- أوامر CLI لتحليل مستندات، استدعاء النماذج، واختبار الاتصال
- دعم تشغيل محلي بدون واجهة ويب

تشغيل سريع (CLI):

1. إعداد البيئة:
   - Python 3.10+
   - إنشاء بيئة افتراضية:
     ```bash
     python -m venv .venv
     source .venv/bin/activate   # عل�� ويندوز: .venv\Scripts\activate
     pip install -r requirements.txt
     ```

2. إعداد المتغيرات البيئية (يمكنك إنشاء ملف `.env`):
   - `API_KEY` - مفتاح المزود السحابي (OpenAI/Anthropic/HuggingFace) إن رغبت
   - `PRESET_NAME` - اسم النموذج الافتراضي من ai_engine.PRESET_NAMES
   - أمثلة أخرى: `CUSTOM_URL`, `CUSTOM_MODEL`, `CUSTOM_FMT`

3. استخدام CLI:
   - استخراج ومعالجة ملفات:
     ```bash
     python fuhrer.py process path/to/doc1.pdf path/to/doc2.docx
     ```
   - تحليل نص عبر النموذج:
     ```bash
     python fuhrer.py analyze "ضع هنا سؤالك أو بيانات التحليل"
     ```
   - عرض النماذج المتاحة:
     ```bash
     python fuhrer.py list-models
     ```
   - اختبار الاتصال بنموذج:
     ```bash
     python fuhrer.py test-conn --preset "GPT-4o 🏆" --api-key "$OPENAI_KEY"
     ```

ملاحظات تقنية:
- تمت إزالة كل تبعيات واجهة Streamlit والاعتماد على واجهة سطر الأوامر لتشغيل التطبيق محليًا.
- المشروع يدعم العمل بنموذج هجيني: محليًا عبر إعدادات نماذج مثل LM Studio/Hugging Face المحلية، ثم الرجوع لمزود سحابي عند الحاجة.

لمزيد من التطوير: يمكنك إضافة واجهة ويب جديدة (FastAPI/Flask) أو دمج llama.cpp/ollama كتوفير نموذج محلي أسرع.
