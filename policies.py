"""
policies.py — سياسات عمل منصة فُهرار القانونية.

تُحدّد هذه الوحدة القواعد التشغيلية لكل مرحلة من مراحل العمل:
التحليل، الصياغة، التحقق، استخدام الأنظمة، الاستشهاد، وإدارة المخاطر.
"""

ANALYSIS_POLICY = {
    "min_aspects":      3,   # الحد الأدنى للجوانب التي يجب تغطيتها في التحليل
    "require_citation": True,
    "require_summary":  True,
    "lang":             "ar",
}

FORMULATION_POLICY = {
    "require_party_names": True,   # يجب تحديد أطراف العقد / الوثيقة
    "require_date":        True,
    "require_legal_basis": True,   # يجب ذكر الأساس القانوني
    "formal_language":     True,
}

VERIFICATION_POLICY = {
    "cross_check_articles": True,  # التحقق من تطابق المادة مع محتواها
    "flag_uncertainty":     True,  # الإشارة الصريحة عند عدم اليقين
    "max_confidence_no_text": 0.7, # لا تتجاوز 70% ثقة بدون نص صريح
}

SYSTEM_USE_POLICY = {
    "primary_systems": [
        "نظام العمل السعودي",
        "نظام الخدمة المدنية",
        "نظام التأمينات الاجتماعية",
        "نظام العمال المنزليين",
    ],
    "secondary_systems": [
        "نظام مكافحة الفساد",
        "نظام الإجراءات الجزائية",
        "نظام التحكيم",
    ],
    "out_of_scope": [
        "الأحوال الشخصية",
        "النزاعات التجارية البحتة",
        "القضايا الجنائية",
    ],
}

CITATION_POLICY = {
    "format":       "المادة {number} من {system}",
    "require_text": False,  # لا يُشترط إيراد النص الكامل
    "prefer_exact": True,   # يُفضّل الاستشهاد بالمادة المحددة لا بالفصل
}

RISK_POLICY = {
    "always_disclaim": True,
    "disclaimer_ar": (
        "تنبيه: هذه استشارة إرشادية ولا تُغني عن استشارة محامٍ مُرخَّص "
        "للقضايا ذات الطابع القضائي أو التي تتجاوز الحد المالي المُهم."
    ),
    "escalate_to_lawyer": [
        "فصل تعسفي بمطالبة مالية كبيرة",
        "قضايا أمام المحكمة العمالية",
        "نزاعات جماعية",
        "مخالفات جسيمة مع عقوبات",
    ],
}

INFORMATION_GAP_POLICY = {
    "on_missing_info":  "اطلب المعلومة الناقصة قبل إصدار الرأي.",
    "on_unclear_facts": "اشرح الافتراضات التي بنيت عليها الإجابة.",
    "on_no_text":       "أقرّ بعدم وجود نص صريح وقدّم الرأي الفقهي السائد.",
}


class Policies:
    """سياسات عمل المنصة — مرجع للقرارات التشغيلية."""

    def analysis_policy(self) -> dict:
        return ANALYSIS_POLICY

    def formulation_policy(self) -> dict:
        return FORMULATION_POLICY

    def verification_policy(self) -> dict:
        return VERIFICATION_POLICY

    def system_use_policy(self) -> dict:
        return SYSTEM_USE_POLICY

    def citation_policy(self) -> dict:
        return CITATION_POLICY

    def risk_management_policy(self) -> dict:
        return RISK_POLICY

    def information_gap_policy(self) -> dict:
        return INFORMATION_GAP_POLICY

    def get_disclaimer(self) -> str:
        return RISK_POLICY["disclaimer_ar"]

    def is_in_scope(self, topic: str) -> bool:
        """يتحقق مما إذا كان الموضوع ضمن نطاق اختصاص المنصة."""
        out = SYSTEM_USE_POLICY["out_of_scope"]
        return not any(t in topic for t in out)


policies = Policies()
