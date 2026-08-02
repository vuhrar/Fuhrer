# Führer - النظام القانوني الذكي للقانون العمالي السعودي (CLI + HTTP)

هذا المشروع مُعدّ الآن للعمل محليًا عبر CLI ومع واجهة HTTP بسيطة (FastAPI) حتى تتمكن من الوصول إليه من جهازك (بما في ذلك iPhone) باستخدام مفاتيح API لمزودي النماذج.

ما تم إضافته:
- واجهة HTTP بسيطة (FastAPI) في server.py لاستدعاء وظائف المعالجة والنماذج عبر REST.
- ملف .env.example لتخزين مفاتيح ومحددات الاتصال (OpenAI / Anthropic / HuggingFace / إعدادات مخصصة).
- تكامل كامل مع ai_engine.call_ai (يدعم جميع المزودين الموجودين في ai_engine.PRESETS).
- توجيهات سريعة لتشغيل الخادم محليًا ومن الجهاز المحمول.

متطلبات سريعة:
- Python 3.10+
- تثبيت المتطلبات:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

إعداد المتغيرات (أنشئ ملف .env في جذر المشروع واملأه وفق .env.example)

تشغيل الخادم (محلي):
```bash
# تشغيل خادم FastAPI عبر Uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000
```

استخدام من iPhone (مثال عبر curl أو Shortcuts):
- استدعاء تحليل نص مباشر:
  POST https://<your-host>:8000/analyze
  body JSON: {"prompt": "نص التحليل هنا", "preset_name": "GPT-4o 🏆"}

- رفع ملفات وتحليلها:
  POST https://<your-host>:8000/upload (multipart/form-data) حقل files

أُشير إلى أن تشغيل نموذج محلي فعلي يتطلب موارد — هذا المشروع مصمم للعمل مع نماذج بعيدة عبر مفاتيح API (OpenAI / Anthropic / HuggingFace) ليعمل فورًا من هاتفك.
