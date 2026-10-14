# خيارات استضافة FüLaw المهنية — 2026-10-14

## الترشيح

الاختيار الأنسب لتطبيق FüLaw هو خادم Ubuntu دائم بمواصفات 2–4 vCPU و4–8 GB RAM و80 GB SSD على الأقل، مع Docker وTailscale ونسخ احتياطي يومي منفصل. إذا كانت الأولوية للسهولة والإدارة من داخل Manus، فـ Cloud Computer Standard يعطي 2 vCPU و4 GB RAM و70 GB وتوجد له لقطات يومية حتى 10 نسخ. إذا كانت الأولوية لأقل تكلفة مدفوعة، فـ Hetzner Cloud أو Vultr. إذا كانت الأولوية لشركة سحابية كبرى وتجربة تشغيل سهلة، فـ AWS Lightsail أو DigitalOcean.

## الخيارات

- Oracle Always Free: يصل رصيد Always Free إلى 2 OCPU و12 GB RAM على Ampere A1، مع 200 GB Block Volume وخمس نسخ احتياطية. هو أفضل خيار مجاني، لكن توفر السعة والتسجيل ليسا مضمونين، وقد تُسترد الآلات الخاملة وفق شروط Oracle.
- Hetzner Cloud: صفحة التكلفة تعرض CX23 بموارد 2 vCPU و4 GB و40 GB NVMe، وخططًا أكبر، مع 20 TB نقل في مواقع الاتحاد الأوروبي وادعاء GDPR-compliant. يجب التحقق من التوفر والسعر النهائي في الحساب قبل الإنشاء.
- Vultr Regular Performance: يعرض 2 vCPU و4 GB و80 GB و3 TB نقل بسعر 20 دولارًا شهريًا، أو High Performance بسعر 24 دولارًا لنفس الذاكرة تقريبًا مع 100 GB NVMe و5 TB نقل. النسخ الاحتياطية لقطات إضافية.
- DigitalOcean Basic: يعرض 2 vCPU و4 GiB و80 GiB SSD و4,000 GiB نقل بسعر 24 دولارًا شهريًا. الواجهة والوثائق ممتازة، لكن النسخ الاحتياطية المدارة تضاف إلى التكلفة.
- AWS Lightsail: يعرض 2 vCPU و4 GB و80 GB و4 TB نقل بسعر 24 دولارًا شهريًا، مع IP ثابت وDNS ومراقبة وSSH من اللوحة. مناسب لمن يريد AWS بطريقة مبسطة، وتبقى اللقطات/النسخ الاحتياطية وموارد إضافية ضمن الحساب.
- Azure VM: قوي للمؤسسات والتكاملات، لكن المثال الرسمي D2s v6 (2 vCPU و8 GiB) يقارب 73.73 دولارًا شهريًا قبل الأقراص ونقل البيانات، لذلك هو أعلى كلفة لهذا التطبيق الصغير.
- Manus Cloud Computer Standard: خادم Ubuntu دائم مُدار داخل Manus، 2 vCPU و4 GB و70 GB، بسعر 30 دولارًا شهريًا، مع IP عام ونسخ يومية كاملة حتى 10 نسخ. هو الأسهل للتنفيذ بواسطة Manus، لكنه ليس مجانيًا.

## القرار

للتجربة المجانية: Oracle Always Free.
لأفضل تكلفة مدفوعة: Hetzner Cloud أو Vultr High Performance حسب توفر المنطقة.
لأسهل تشغيل احترافي: Manus Cloud Computer Standard أو AWS Lightsail.
لبيئة مؤسسية: Azure، لكنه غير اقتصادي كبداية.

لا يكفي اختيار المزود وحده لحماية القضايا. يجب تفعيل تشفير ملفات التطبيق، حفظ مفتاح FULAW_STORAGE_KEY منفصلًا، منع المنفذ العام، استخدام Tailscale أو وصول HTTPS محمي، وفصل النسخ الاحتياطية عن الخادم.

## المصادر الرسمية

- https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://www.hetzner.com/cloud/cost-optimized/
- https://www.vultr.com/pricing/
- https://www.digitalocean.com/pricing/droplets
- https://aws.amazon.com/lightsail/pricing/
- https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/
- Manus Cloud Computer reference داخل بيئة المشروع.
