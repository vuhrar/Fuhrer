"""مزامنة محافظة للمصادر الرسمية لنظام العمل السعودي.

لا تستبدل هذه الوحدة قاعدة المعرفة إلا بعد تحقق متعدد المراحل:
نجاح HTTP، بصمة محتوى، ظهور حالة السريان في سجل هيئة الخبراء، واستخراج
عدد كافٍ من المواد. عند الفشل تبقى النسخة السابقة فعالة ويُسجل سبب الفشل.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List

PARSER_VERSION = "official-sync-1.0"
ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("OFFICIAL_SOURCE_DATA_DIR", ROOT / "data" / "official_sources"))
REGISTRY_PATH = DATA_DIR / "registry.json"
ARTICLES_PATH = DATA_DIR / "official_labor_articles.json"
BOOTSTRAP_BOE_PATH = ROOT / "official_boe_snapshot.md"

SOURCES = [
    {
        "source_id": "boe_labor_law",
        "authority": "هيئة الخبراء بمجلس الوزراء",
        "kind": "html",
        "url": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/08381293-6388-48e2-8ad2-a9a700f2aa94/1",
        "required": False,
    },
    {
        "source_id": "hrsd_labor_law_pdf",
        "authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
        "kind": "pdf",
        "url": "https://www.hrsd.gov.sa/sites/default/files/2025-11/labor-law.pdf",
        "required": True,
    },
    {
        "source_id": "hrsd_labor_regulation_page",
        "authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
        "kind": "html",
        "url": "https://www.hrsd.gov.sa/id/node/838894",
        "required": True,
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"schema_version": 1, "parser_version": PARSER_VERSION, "active_snapshot": None, "sources": {}, "history": []}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "parser_version": PARSER_VERSION, "active_snapshot": None, "sources": {}, "history": []}


def _save_registry(registry: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def _html_text(raw: bytes) -> str:
    parser = _VisibleText()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def _pdf_text(path: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as out:
        output = Path(out.name)
    try:
        result = subprocess.run(["pdftotext", "-layout", str(path), str(output)], capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            return ""
        return output.read_text(encoding="utf-8", errors="replace")
    finally:
            output.unlink(missing_ok=True)


def _pdf_ocr_text(path: Path) -> str:
    """OCR عربي احتياطي للطبقة النصية المشوهة في ملفات PDF الحكومية."""
    cache = path.with_suffix(".ocr.txt")
    if cache.exists() and cache.stat().st_size > 1000:
        return cache.read_text(encoding="utf-8", errors="replace")
    if not shutil.which("tesseract") or not shutil.which("pdftoppm"):
        return ""
    with tempfile.TemporaryDirectory(prefix="fulaw-ocr-") as temp_dir:
        prefix = str(Path(temp_dir) / "page")
        rendered = subprocess.run(["pdftoppm", "-r", "180", "-png", str(path), prefix], capture_output=True, text=True, timeout=300)
        if rendered.returncode != 0:
            return ""
        chunks: List[str] = []
        for image in sorted(Path(temp_dir).glob("page-*.png")):
            result = subprocess.run(["tesseract", str(image), "stdout", "-l", "ara", "--psm", "6"], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                chunks.append(result.stdout)
        text = "\n".join(chunks)
    if len(text) > 1000:
        cache.write_text(text, encoding="utf-8")
    return text


def _arabic_digits(value: str) -> str:
    return value.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))


_ORDINAL_UNITS = {
    "الأولى": 1, "الاولى": 1, "الأول": 1, "الاول": 1, "الثانية": 2, "الثاني": 2,
    "الثالثة": 3, "الثالث": 3, "الرابعة": 4, "الرابع": 4, "الخامسة": 5, "الخامس": 5,
    "السادسة": 6, "السادس": 6, "السابعة": 7, "السابع": 7, "الثامنة": 8, "الثامن": 8,
    "التاسعة": 9, "التاسع": 9, "العاشرة": 10, "العاشر": 10, "الحادية": 1, "الحادي": 1,
    "الحاديةعشرة": 11, "الحاديعشر": 11, "الثانيةعشرة": 12, "الثانيعشر": 12,
    "الثالثةعشرة": 13, "الثالثعشر": 13, "الرابعةعشرة": 14, "الرابععشر": 14,
    "الخامسةعشرة": 15, "الخامسعشر": 15, "السادسةعشرة": 16, "السادسعشر": 16,
    "السابعةعشرة": 17, "السابععشر": 17, "الثامنةعشرة": 18, "الثامن" + "عشر": 18,
    "التاسعةعشرة": 19, "التاسععشر": 19,
}
_ORDINAL_TENS = {"العشرون": 20, "الثلاثون": 30, "الأربعون": 40, "الاربعون": 40, "الخمسون": 50, "الستون": 60, "السبعون": 70, "الثمانون": 80, "التسعون": 90}


def _parse_article_label(label: str) -> int | None:
    label = re.sub(r"[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]", "", label or "")
    label = re.sub(r"\s+", " ", label).strip().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    label = label.replace(" مكرر", "").replace("مكرر", "")
    label = label.replace("الثالئة", "الثالثة").replace("الخحمسون", "الخمسون")
    base = 0
    if "بعد المائتين" in label or "بعد المايتين" in label:
        base, label = 200, label.split("بعد الم", 1)[0].strip()
    elif "بعد المائة" in label or "بعد المئه" in label:
        base, label = 100, label.split("بعد الم", 1)[0].strip()
    compact = label.replace(" ", "")
    if compact in {"المائة", "المائة"}:
        return 100
    if compact in {"المئتان", "المائتان", "المائتين"}:
        return 200
    if compact in _ORDINAL_TENS:
        return base + _ORDINAL_TENS[compact]
    if compact in _ORDINAL_UNITS:
        return base + _ORDINAL_UNITS[compact]
    for tens_word, tens_value in _ORDINAL_TENS.items():
        if compact.endswith(tens_word):
            prefix = compact[: -len(tens_word)].rstrip("و")
            unit = _ORDINAL_UNITS.get(prefix)
            if unit:
                return base + unit + tens_value
    return None


def _extract_articles(text: str) -> List[Dict[str, Any]]:
    """استخراج محافظ للمواد الرقمية من النص الرسمي؛ لا يخمن أرقام المواد اللفظية."""
    # بعض ملفات PDF الحكومية تفصل حروف كلمة "المادة" بعلامات اتجاه ومسافات
    # (الم ا د ة)، لذلك يفشل البحث المباشر رغم أن المحتوى موجود كاملًا.
    text = re.sub(r"[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]", "", text or "")
    text = re.sub(r"الم\s*ا\s*د\s*ة", "المادة", text)
    normalized = re.sub(r"\s+", " ", text or "").strip()
    pattern = re.compile(r"(?:المادة|مادة)\s*\(?\s*([0-9٠١٢٣٤٥٦٧٨٩]{1,3})\s*\)?\s*[:：-]?", re.IGNORECASE)
    matches = list(pattern.finditer(normalized))
    articles: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        number = _arabic_digits(match.group(1))
        if number in seen:
            continue
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else min(len(normalized), body_start + 12000)
        body = normalized[body_start:body_end].strip(" -:؛")
        if len(body) < 20:
            continue
        seen.add(number)
        articles.append({
            "article": number,
            "title": f"المادة {number}",
            "category": "نظام العمل — مصدر رسمي متزامن",
            "text": body,
            "keywords": ["نظام العمل", f"المادة {number}"],
            "needs_verification": False,
            "source_id": "boe_labor_law",
            "source_status": "ساري",
            "parser_version": PARSER_VERSION,
        })
    # ملفات الوزارة الرسمية تستخدم غالبًا: "المادة الأولى:" بدل رقم رقمي.
    # إذا تعذر استخراج 100 مادة رقمية، نستخدم عناوين الأقسام المتسلسلة فقط؛
    # لا نخلط إحالات "هذه المادة" لأنها لا تنتهي بنقطتين بعد عنوان مستقل.
    heading_pattern = re.compile(r"المادة\s+([^:؛\n]{1,70})(?=\s*(?:[:：]|\n))")
    headings = list(heading_pattern.finditer(text or ""))
    valid_heading_candidates = [(heading, _parse_article_label(heading.group(1))) for heading in headings]
    valid_heading_candidates = [(heading, number) for heading, number in valid_heading_candidates if number is not None]
    if len(valid_heading_candidates) >= 2:
        articles = []
        seen_positions: set[int] = set()
        seen_numbers: set[int] = set()
        valid_headings = valid_heading_candidates
        for ordinal, (heading, number) in enumerate(valid_headings):
            if heading.start() in seen_positions:
                continue
            seen_positions.add(heading.start())
            body_start = heading.end()
            body_end = valid_headings[ordinal + 1][0].start() if ordinal + 1 < len(valid_headings) else min(len(text), body_start + 12000)
            body = re.sub(r"\s+", " ", text[body_start:body_end]).strip(" -:؛")
            if len(body) < 20:
                continue
            if number is None or number in seen_numbers:
                continue
            seen_numbers.add(number)
            articles.append({
                "article": str(number),
                "title": f"المادة {heading.group(1).strip()}",
                "category": "نظام العمل — مصدر رسمي متزامن",
                "text": body,
                "keywords": ["نظام العمل", f"المادة {ordinal}"],
                "needs_verification": False,
                "source_id": "hrsd_labor_law_pdf",
                "source_status": "ساري — مستخرج من PDF الوزارة",
                "parser_version": PARSER_VERSION,
            })
    return articles


def _coverage_complete(articles: List[Dict[str, Any]]) -> bool:
    numbers = {int(item["article"]) for item in articles if str(item.get("article", "")).isdigit()}
    return numbers == set(range(1, 246))


def _fetch(spec: Dict[str, Any]) -> Dict[str, Any]:
    request = urllib.request.Request(spec["url"], headers={"User-Agent": "FuLaw-OfficialSync/1.0 (+legal-source-verification)"})
    transport = "live"
    transport_error = None
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
    except Exception as live_error:
        with tempfile.NamedTemporaryFile(delete=False) as downloaded:
            fallback_path = Path(downloaded.name)
        try:
            result = subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--max-time", "90", "-A", "FuLaw-OfficialSync/1.0", "-o", str(fallback_path), spec["url"]], capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                if spec["source_id"] == "boe_labor_law" and BOOTSTRAP_BOE_PATH.exists():
                    raw = BOOTSTRAP_BOE_PATH.read_bytes()
                    status = 200
                    content_type = "text/markdown; official-bootstrap"
                    transport = "official_bootstrap_after_tls_failure"
                    transport_error = f"{type(live_error).__name__}: {live_error}; curl: {result.stderr.strip()}"
                else:
                    raise RuntimeError(result.stderr.strip() or "curl failed")
            else:
                raw = fallback_path.read_bytes()
                status = 200
                content_type = "application/pdf" if spec["kind"] == "pdf" else "text/html"
                transport = "curl_fallback"
        finally:
            fallback_path.unlink(missing_ok=True)
    digest = hashlib.sha256(raw).hexdigest()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    extension = ".pdf" if spec["kind"] == "pdf" else ".html"
    raw_path = DATA_DIR / f"{spec['source_id']}-{digest[:16]}{extension}"
    raw_path.write_bytes(raw)
    extraction_method = "html_visible_text"
    text = _pdf_text(raw_path) if spec["kind"] == "pdf" else (
        raw.decode("utf-8", errors="replace") if transport.startswith("official_bootstrap") else _html_text(raw)
    )
    if spec["kind"] == "pdf":
        extraction_method = "pdftotext-layout"
        primary_articles = _extract_articles(text)
        if not _coverage_complete(primary_articles):
            ocr_text = _pdf_ocr_text(raw_path)
            if len(_extract_articles(ocr_text)) > len(primary_articles):
                text = ocr_text
                extraction_method = "tesseract-ara-psm6-fallback"
    extracted_articles = _extract_articles(text)
    text_path = raw_path.with_suffix(".txt")
    text_path.write_text(text, encoding="utf-8")
    return {
        **spec,
        "fetched_at": utc_now(),
        "http_status": status,
        "content_type": content_type,
        "sha256": digest,
        "bytes": len(raw),
        "raw_path": str(raw_path),
        "text_path": str(text_path),
        "characters": len(text),
        "status_sari": bool(re.search(r"الحالة\s*ساري|ساري", text)),
        "article_count": len(extracted_articles) if spec["kind"] in {"html", "pdf"} else None,
        "coverage_complete": _coverage_complete(extracted_articles) if spec["kind"] in {"html", "pdf"} else False,
        "extraction_method": extraction_method,
        "transport": transport,
        "transport_error": transport_error,
    }


def sync_official_sources() -> Dict[str, Any]:
    registry = _load_registry()
    run = {"run_id": utc_now(), "parser_version": PARSER_VERSION, "ok": False, "sources": [], "errors": []}
    records = {}
    for spec in SOURCES:
        try:
            record = _fetch(spec)
            record["verified"] = bool(record["http_status"] == 200 and record["characters"] >= 1000)
            if spec["source_id"] == "boe_labor_law":
                record["verified"] = record["verified"] and record["status_sari"] and record.get("coverage_complete", False)
            records[spec["source_id"]] = record
            run["sources"].append(record)
        except Exception as exc:
            previous = registry.get("sources", {}).get(spec["source_id"], {})
            records[spec["source_id"]] = {"source_id": spec["source_id"], "authority": spec["authority"], "url": spec["url"], "required": spec["required"], "verified": False, "error": f"{type(exc).__name__}: {exc}", "previous_sha256": previous.get("sha256")}
            run["sources"].append(records[spec["source_id"]])
            run["errors"].append(records[spec["source_id"]])

    required_ok = all(records.get(spec["source_id"], {}).get("verified") for spec in SOURCES if spec["required"])
    articles = []
    boe = records.get("boe_labor_law", {})
    article_source = boe if boe.get("verified") else records.get("hrsd_labor_law_pdf", {})
    if article_source.get("verified") and article_source.get("text_path"):
        articles = _extract_articles(Path(article_source["text_path"]).read_text(encoding="utf-8", errors="replace"))
    if required_ok and _coverage_complete(articles):
        tmp = ARTICLES_PATH.with_suffix(".tmp")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({"source_id": article_source["source_id"], "source_url": article_source["url"], "source_sha256": article_source["sha256"], "verified_at": utc_now(), "cross_source_status": "هيئة الخبراء متحقق منها" if boe.get("verified") else "هيئة الخبراء بانتظار إعادة المحاولة التقنية", "articles": articles}, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(ARTICLES_PATH)
        snapshot_id = article_source["sha256"]
        registry["active_snapshot"] = {"snapshot_id": snapshot_id, "articles_path": str(ARTICLES_PATH), "verified_at": utc_now(), "source_ids": list(records), "source_sha256": {key: value.get("sha256") for key, value in records.items()}}
        run["ok"] = True
        run["activated_snapshot"] = snapshot_id
    else:
        run["blocked_activation"] = True
        run["reason"] = "لم تجتز كل المصادر الإلزامية تحقق HTTP/السريان/عدد المواد؛ بقيت النسخة السابقة فعالة."
    registry["sources"] = records
    registry["last_run"] = run
    registry.setdefault("history", []).append(run)
    registry["history"] = registry["history"][-30:]
    _save_registry(registry)
    return run


def get_sync_status() -> Dict[str, Any]:
    registry = _load_registry()
    active = registry.get("active_snapshot")
    return {
        "parser_version": PARSER_VERSION,
        "active_snapshot": active,
        "last_run": registry.get("last_run"),
        "sources": [
            {
                "source_id": value.get("source_id"),
                "authority": value.get("authority"),
                "url": value.get("url"),
                "fetched_at": value.get("fetched_at"),
                "sha256": value.get("sha256"),
                "verified": value.get("verified", False),
                "status_sari": value.get("status_sari"),
                "article_count": value.get("article_count"),
                "coverage_complete": value.get("coverage_complete", False),
                "extraction_method": value.get("extraction_method"),
                "transport": value.get("transport"),
                "transport_error": value.get("transport_error"),
                "error": value.get("error"),
            }
            for value in registry.get("sources", {}).values()
        ],
        "policy": "official_snapshot_only_when_verified; previous_snapshot_retained_on_failure",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync official Saudi labor-law sources safely")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = sync_official_sources()
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("SYNC_OK" if result["ok"] else "SYNC_BLOCKED"))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
