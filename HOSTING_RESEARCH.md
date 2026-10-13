# نتائج فحص الاستضافة المجانية

- Oracle Cloud Free Tier: https://www.oracle.com/cloud/free/ و https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm — يقدم موارد Always Free وقد يتطلب التسجيل وبطاقة، وتوافر VM ليس مضمونًا.
- Tailscale Personal: https://tailscale.com/pricing و https://tailscale.com/docs/account/manage-plans/free-plans-discounts — مناسب لربط خادم خاص وأجهزة المستخدم بشبكة خاصة، لكنه لا يوفر VM بذاته.
- GitHub Actions billing: https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions — مناسب للبناء والنشر المحدود، وليس مخزنًا آمنًا لملفات القضايا أو خدمة VM دائمة.

القرار الهندسي: عدم رفع ملفات القضايا إلى GitHub أو استضافة مجانية عامة. جعل التطبيق قابلًا للنشر على VM يملكه المستخدم، مع تشفير محلي، وطرح Oracle Free كخيار يحتاج إنشاء الحساب والموافقة من المستخدم. البديل المجاني الأكثر خصوصية هو جهاز المستخدم المتصل دائمًا أو My Computer مع شبكة خاصة مثل Tailscale.
