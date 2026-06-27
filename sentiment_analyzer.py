# sentiment_analyzer.py
"""
محلل النبرة والتصعيد واكتشاف الإقرارات والتهديدات.
"""
import re
from typing import List, Dict, Any, Optional
from collections import Counter

class SentimentAnalyzer:
    """محلل النبرة والتصعيد في المراسلات"""

    def __init__(self):
        # قوائم الكلمات المفتاحية للتصنيف
        self.threat_keywords = ["تهديد", "فصل", "إيقاف", "حرمان", "عقاب", "جزاء", "محاكمة", "مسؤولية", "عواقب"]
        self.acknowledgment_keywords = ["أقر", "اعترف", "أعترف", "نعترف", "مقر", "معترف", "صحيح", "صحيحاً"]
        self.offer_keywords = ["صلح", "تسوية", "تفاهم", "اتفاق", "عرض", "نقترح", "نحن مستعدون"]
        self.apology_keywords = ["اعتذار", "آسف", "نأسف", "خطأ", "ندم"]
        self.demand_keywords = ["يطالب", "مطالبة", "نطالب", "إلزام", "وجوب", "لابد"]
        self.escalation_keywords = ["آخر إنذار", "نهائي", "آخر فرصة", "إجراءات قانونية", "محكمة", "دعوى"]
        self.deescalation_keywords = ["تفهم", "نقدر", "نرحب", "حوار", "بناء", "إيجابي"]

    def analyze_text(self, text: str, sender: str = "unknown") -> Dict[str, Any]:
        """
        تحليل نص واحد (رسالة بريد أو مراسلة)
        """
        text_lower = text.lower()
        analysis = {
            "sender": sender,
            "length": len(text),
            "message_type": self._classify_message(text_lower),
            "sentiment": self._analyze_sentiment(text_lower),
            "is_threat": self._contains_threat(text_lower),
            "is_acknowledgment": self._contains_acknowledgment(text_lower),
            "is_offer": self._contains_offer(text_lower),
            "is_apology": self._contains_apology(text_lower),
            "is_escalation": self._contains_escalation(text_lower),
            "key_phrases": self._extract_key_phrases(text_lower),
            "legal_risks": self._identify_legal_risks(text_lower),
        }
        return analysis

    def analyze_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        تحليل سلسلة من المراسلات (محادثة)
        يعيد التصنيفات، منحنى التصعيد، وتحليل نبرة كل طرف.
        """
        if not messages:
            return {"error": "لا توجد رسائل للتحليل"}

        analysis = {
            "messages": [],
            "escalation_curve": [],
            "sender_profiles": {},
            "overall_tone": "محايد",
            "risks": [],
            "summary": ""
        }

        # تحليل كل رسالة
        for msg in messages:
            text = msg.get("content", "")
            sender = msg.get("sender", "unknown")
            ts = msg.get("ts", "")
            result = self.analyze_text(text, sender)
            result["ts"] = ts
            analysis["messages"].append(result)

            # تحديث منحنى التصعيد (يعتمد على درجة التهديد والتصعيد)
            escalation_score = 0
            if result["is_threat"]:
                escalation_score += 2
            if result["is_escalation"]:
                escalation_score += 2
            if result["is_offer"]:
                escalation_score -= 1
            if result["is_apology"]:
                escalation_score -= 1
            analysis["escalation_curve"].append(escalation_score)

            # تحديث ملفات المرسلين
            if sender not in analysis["sender_profiles"]:
                analysis["sender_profiles"][sender] = {"threats": 0, "offers": 0, "apologies": 0, "acknowledgments": 0}
            if result["is_threat"]:
                analysis["sender_profiles"][sender]["threats"] += 1
            if result["is_offer"]:
                analysis["sender_profiles"][sender]["offers"] += 1
            if result["is_apology"]:
                analysis["sender_profiles"][sender]["apologies"] += 1
            if result["is_acknowledgment"]:
                analysis["sender_profiles"][sender]["acknowledgments"] += 1

        # تحديد النبرة العامة
        if any(msg["is_threat"] for msg in analysis["messages"]):
            analysis["overall_tone"] = "عدائي (يحتوي على تهديدات)"
        elif any(msg["is_offer"] for msg in analysis["messages"]):
            analysis["overall_tone"] = "تفاوضي (يحتوي على عروض صلح)"
        elif any(msg["is_apology"] for msg in analysis["messages"]):
            analysis["overall_tone"] = "اعتذاري (يحتوي على اعتذارات)"
        else:
            analysis["overall_tone"] = "محايد"

        # تحليل نقاط الضعف (risks)
        analysis["risks"] = self._identify_conversation_risks(analysis)
        analysis["summary"] = self._generate_conversation_summary(analysis)

        return analysis

    def _classify_message(self, text: str) -> str:
        """تصنيف نوع الرسالة"""
        if self._contains_threat(text):
            return "تهديد"
        if self._contains_acknowledgment(text):
            return "إقرار"
        if self._contains_offer(text):
            return "عرض صلح"
        if self._contains_apology(text):
            return "اعتذار"
        if self._contains_demand(text):
            return "مطالبة"
        if self._contains_escalation(text):
            return "تصعيد"
        if self._contains_deescalation(text):
            return "تهدئة"
        return "عام"

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """تحليل النبرة العاطفية"""
        positive = ["شكر", "تفهم", "نقدر", "نرحب", "بناء", "إيجابي", "ممتاز", "جيد", "حسن"]
        negative = ["سيء", "فاشل", "خطير", "مرفوض", "غير مقبول", "كارثة", "مشكلة", "فشل", "تجاهل", "إهمال"]
        neutral = ["عادي", "طبيعي", "معتاد", "متوقع"]

        pos_count = sum(1 for w in positive if w in text)
        neg_count = sum(1 for w in negative if w in text)
        neu_count = sum(1 for w in neutral if w in text)

        if pos_count > neg_count and pos_count > neu_count:
            return {"label": "إيجابي", "score": pos_count / (pos_count + neg_count + 1)}
        elif neg_count > pos_count and neg_count > neu_count:
            return {"label": "سلبي", "score": neg_count / (pos_count + neg_count + 1)}
        else:
            return {"label": "محايد", "score": 0.5}

    def _contains_threat(self, text: str) -> bool:
        return any(kw in text for kw in self.threat_keywords)

    def _contains_acknowledgment(self, text: str) -> bool:
        return any(kw in text for kw in self.acknowledgment_keywords)

    def _contains_offer(self, text: str) -> bool:
        return any(kw in text for kw in self.offer_keywords)

    def _contains_apology(self, text: str) -> bool:
        return any(kw in text for kw in self.apology_keywords)

    def _contains_demand(self, text: str) -> bool:
        return any(kw in text for kw in self.demand_keywords)

    def _contains_escalation(self, text: str) -> bool:
        return any(kw in text for kw in self.escalation_keywords)

    def _contains_deescalation(self, text: str) -> bool:
        return any(kw in text for kw in self.deescalation_keywords)

    def _extract_key_phrases(self, text: str) -> List[str]:
        """استخراج العبارات المفتاحية"""
        phrases = []
        # استخراج الجمل التي تحتوي على كلمات مفتاحية
        sentences = re.split(r'[.،\n]', text)
        for sent in sentences:
            if any(kw in sent for kw in self.threat_keywords + self.acknowledgment_keywords + self.offer_keywords):
                phrases.append(sent.strip()[:100])
        return phrases[:5]

    def _identify_legal_risks(self, text: str) -> List[str]:
        """تحديد المخاطر القانونية في النص"""
        risks = []
        if "استقالة" in text and "مكافأة" not in text:
            risks.append("⚠️ ذكر 'استقالة' دون ذكر 'مكافأة' قد يُفقدك حقك في المكافأة الكاملة (المادة 85 من نظام العمل). يُنصح بتوضيح أن الاستقالة كانت تحت الإكراه.")
        if "فصل" in text and "تحقيق" not in text:
            risks.append("⚠️ ذكر 'فصل' دون 'تحقيق' قد يعني فصل تعسفي (المادة 80 من نظام العمل). الفصل دون تحقيق باطل.")
        if "تأخير" in text and "راتب" in text:
            risks.append("⚠️ التأخير في الراتب يُخوّلك للمطالبة بتعويض (المادة 90 من نظام العمل).")
        return risks

    def _identify_conversation_risks(self, analysis: Dict) -> List[str]:
        """تحديد مخاطر المحادثة الكاملة"""
        risks = []
        profiles = analysis.get("sender_profiles", {})
        for sender, profile in profiles.items():
            if profile.get("threats", 0) >= 2:
                risks.append(f"⚠️ الطرف '{sender}' كرر التهديدات ({profile['threats']} مرات)، مما يُعتبر تعسفاً في استعمال الحق.")
            if profile.get("acknowledgments", 0) >= 1:
                risks.append(f"✅ الطرف '{sender}' قدّم إقرارات كتابية ({profile['acknowledgments']} مرة)، وهي حجة قاطعة ضده (المادة 17 من نظام الإثبات).")
        return risks

    def _generate_conversation_summary(self, analysis: Dict) -> str:
        """توليد ملخص المحادثة"""
        summary = f"تم تحليل {len(analysis['messages'])} رسالة. النبرة العامة: {analysis['overall_tone']}. "
        threats = sum(1 for m in analysis['messages'] if m.get('is_threat'))
        acks = sum(1 for m in analysis['messages'] if m.get('is_acknowledgment'))
        offers = sum(1 for m in analysis['messages'] if m.get('is_offer'))
        summary += f"عدد التهديدات: {threats}, الإقرارات: {acks}, عروض الصلح: {offers}."
        if threats > 0:
            summary += " يُنصح بتوثيق التهديدات كدليل على التعسف."
        if acks > 0:
            summary += " الإقرارات المكتشفة تعزز موقفك القانوني بشكل كبير."
        return summary