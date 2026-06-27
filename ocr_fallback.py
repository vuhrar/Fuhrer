# ocr_fallback.py
"""
طبقة OCR احتياطية لاستخراج النصوص من الملفات الممسوحة ضوئياً (Scanned PDF/Images).
تستخدم pytesseract + pdf2image كحل بديل عندما تفشل القراءة الرقمية المباشرة.
"""
import io
import logging
from typing import Optional, List
from PIL import Image

logger = logging.getLogger(__name__)

class OCRFallback:
    """
    محلل OCR احتياطي للملفات الممسوحة ضوئياً.
    يحول صفحات PDF إلى صور ثم يستخرج النصوص باستخدام Tesseract.
    """

    def __init__(self, lang: str = "ara+eng"):
        """
        Args:
            lang: لغة OCR (افتراضي: عربية + إنجليزية)
        """
        self.lang = lang
        self._initialized = False

    def _initialize(self):
        """التحقق من توفر المكتبات المطلوبة"""
        if self._initialized:
            return
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
            self._tesseract = pytesseract
            self._convert_from_bytes = convert_from_bytes
            self._initialized = True
            logger.info("OCR Fallback initialized successfully")
        except ImportError as e:
            logger.error(f"OCR libraries not available: {e}")
            self._initialized = False
            raise ImportError(
                "OCR libraries (pytesseract, pdf2image, PIL) are required. "
                "Run: pip install pytesseract pdf2image pillow"
            )

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        استخراج النص من صورة (JPEG, PNG, BMP, TIFF)
        """
        self._initialize()
        try:
            img = Image.open(io.BytesIO(image_bytes))
            text = self._tesseract.image_to_string(img, lang=self.lang)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed on image: {e}")
            return ""

    def extract_text_from_pdf(self, pdf_bytes: bytes, dpi: int = 200) -> str:
        """
        استخراج النص من PDF ممسوح ضوئياً (جميع الصفحات)
        """
        self._initialize()
        try:
            images = self._convert_from_bytes(pdf_bytes, dpi=dpi)
            all_text = []
            for i, img in enumerate(images):
                logger.debug(f"Processing page {i+1}/{len(images)}")
                text = self._tesseract.image_to_string(img, lang=self.lang)
                if text.strip():
                    all_text.append(f"--- صفحة {i+1} ---\n{text.strip()}")
                else:
                    all_text.append(f"--- صفحة {i+1} (فارغة أو غير مقروءة) ---")
            return "\n\n".join(all_text)
        except Exception as e:
            logger.error(f"OCR failed on PDF: {e}")
            return ""

    def extract_text_from_file(self, file_content: bytes, file_type: str) -> str:
        """
        استخراج النص من أي ملف (PDF أو صورة)
        """
        self._initialize()
        if file_type in ["pdf"]:
            return self.extract_text_from_pdf(file_content)
        elif file_type in ["png", "jpg", "jpeg", "bmp", "tiff"]:
            return self.extract_text_from_image(file_content)
        else:
            logger.warning(f"Unsupported file type for OCR: {file_type}")
            return ""

    def is_available(self) -> bool:
        """التحقق من توفر OCR"""
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
            return True
        except ImportError:
            return False

    def is_scanned_pdf(self, pdf_bytes: bytes) -> bool:
        """
        محاولة تخمين ما إذا كان PDF ممسوحاً ضوئياً
        بالتحقق من وجود نص قابل للاستخراج في الصفحات.
        """
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            total_chars = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                total_chars += len(text.strip())
            # إذا كان النص أقل من 100 حرف لكل 5 صفحات، يعتبر ممسوحاً
            avg_chars = total_chars / max(1, len(reader.pages))
            return avg_chars < 20
        except Exception:
            return True  # إذا فشل القراءة، نفترض أنه ممسوح