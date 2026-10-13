"""Führer PWA API: المسار التشغيلي الوحيد للتطبيق."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import io
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

import ai_engine
import file_processing
import document_inspection_engine
import hidden_rights_engine
import workspace_store
import reporting
import case_package
import matter_intelligence as intelligence_engine
import advanced_dispute_engine
import legal_case_theory
from evidence_fusion import fuse_text_with_evidence
from repository import repository_from_env
from legal_tools import legal_classifier, info_extractor, entitlement_calculator, evidence_scorer, lawsuit_drafter, litigation_timeline, deadline_engine, termination_assessment, full_entitlements_worksheet
from amicable_settlement import AmicableSettlementRequestDrafter, SettlementOfferReviewer, pre_signature_checklist, DISPUTE_SUBJECT_CATEGORIES

amicable_drafter = AmicableSettlementRequestDrafter()
settlement_reviewer = SettlementOfferReviewer()
from legal_intelligence import OFFICIAL_SOURCES, evidence_checklist, extract_obligations, legal_review_package, procedure_requirements, scan_risks, search_with_sources

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
APP_TOKEN = os.getenv("APP_ACCESS_TOKEN", "").strip()
MAX_FILES = int(os.getenv("MAX_FILES", "5"))
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", str(25 * 1024 * 1024)))

app = FastAPI(title="Führer Personal Legal PWA", version="3.0.0", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(WEB_DIR, "static")), name="static")
legal_repository = repository_from_env()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        if request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response


app.add_middleware(SecurityHeadersMiddleware)


class AnalyzeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=50000)
    system: str = Field(default="", max_length=10000)
    preset_name: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    category: Optional[str] = None
    max_results: int = Field(default=10, ge=1, le=20)


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)


class MatterCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    matter_type: str = Field(default="عام", max_length=80)
    status: str = Field(default="مفتوحة", max_length=40)
    priority: str = Field(default="متوسطة", max_length=30)
    client_name: str = Field(default="", max_length=200)
    opposing_party: str = Field(default="", max_length=200)
    jurisdiction: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=5000)


class MatterUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    matter_type: Optional[str] = Field(default=None, max_length=80)
    status: Optional[str] = Field(default=None, max_length=40)
    priority: Optional[str] = Field(default=None, max_length=30)
    client_name: Optional[str] = Field(default=None, max_length=200)
    opposing_party: Optional[str] = Field(default=None, max_length=200)
    jurisdiction: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)


class ClaimEvidenceRequest(BaseModel):
    claim_id: str = Field(min_length=2, max_length=80)
    document_id: str = Field(min_length=2, max_length=80)
    note: str = Field(default="", max_length=2000)


class TaskRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    status: str = Field(default="مفتوحة", max_length=40)
    priority: str = Field(default="متوسطة", max_length=30)
    due_date: Optional[str] = Field(default=None, max_length=30)
    owner: str = Field(default="المستخدم الوحيد", max_length=120)
    notes: str = Field(default="", max_length=2000)


class PartyRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    role: str = Field(min_length=2, max_length=100)
    contact: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=2000)


class FactRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    event_date: Optional[str] = Field(default=None, max_length=30)
    description: str = Field(default="", max_length=5000)
    certainty: str = Field(default="غير متحقق", max_length=50)
    source_document_id: Optional[str] = Field(default=None, max_length=100)


class ClaimRequest(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    position: str = Field(default="مقترح", max_length=80)
    legal_basis: str = Field(default="", max_length=2000)
    status: str = Field(default="قيد التحقق", max_length=80)
    notes: str = Field(default="", max_length=3000)


class DeadlineRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    due_date: Optional[str] = Field(default=None, max_length=30)
    status: str = Field(default="مفتوح", max_length=50)
    source: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=2000)


class EvidenceItem(BaseModel):
    type: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)
    date: str = Field(default="", max_length=30)


class EvidenceScoreRequest(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


class SeveranceRequest(BaseModel):
    basic_salary: float = Field(gt=0)
    years_of_service: float = Field(ge=0)
    resignation: bool = False


class ArbitraryDismissalRequest(BaseModel):
    total_salary: float = Field(gt=0)
    years_of_service: float = Field(ge=0)


class OvertimeRequest(BaseModel):
    hourly_rate: float = Field(gt=0)
    overtime_hours: float = Field(ge=0)


class AnnualLeaveRequest(BaseModel):
    start_date: str = Field(min_length=8, max_length=20)
    end_date: str = Field(default="", max_length=20)


class WageDelayRequest(BaseModel):
    days_delayed: int = Field(ge=0)


class LawsuitDraftRequest(BaseModel):
    plaintiff_name: str = Field(default="", max_length=200)
    plaintiff_id: str = Field(default="", max_length=50)
    defendant_name: str = Field(default="", max_length=200)
    facts: List[str] = Field(default_factory=list)
    claims: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    articles: List[str] = Field(default_factory=list)


class ClaimAmountTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    claim_amount: Optional[float] = Field(default=None, ge=0)


class PrescriptionRequest(BaseModel):
    reference_date: str = Field(min_length=8, max_length=10, description="YYYY-MM-DD")
    claim_type: str = Field(default="عقد", description="'عقد' أو 'إصابة عمل'")


class AllDeadlinesRequest(BaseModel):
    termination_date: str = Field(min_length=8, max_length=10)
    claim_type: str = Field(default="عقد")
    notice_given_days: Optional[int] = Field(default=None, ge=0)
    monthly_paid: bool = True


class TerminationAssessmentRequest(BaseModel):
    initiated_by: str = Field(description="'صاحب العمل' أو 'العامل'")
    notice_given_days: int = Field(default=0, ge=0)
    monthly_paid: bool = True
    employer_claimed_ground: Optional[str] = None
    worker_claimed_ground: Optional[str] = None


class CorrespondenceItemIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    date: Optional[str] = Field(default=None, max_length=10, description="YYYY-MM-DD إن توفر")
    channel: Optional[str] = Field(default=None, max_length=50, description="بريد رسمي / واتساب / منصة حكومية ...")


class CorrespondenceIngestRequest(BaseModel):
    items: List[CorrespondenceItemIn] = Field(min_length=1, max_length=200)


class AmicableSettlementFactIn(BaseModel):
    date: Optional[str] = Field(default=None, max_length=10)
    text: str = Field(min_length=1, max_length=2000)


class AmicableSettlementClaimIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    legal_basis: str = Field(default="", max_length=200)
    amount: Optional[float] = Field(default=None, ge=0)


class AmicableSettlementDraftRequest(BaseModel):
    plaintiff_name: str = Field(default="", max_length=200)
    plaintiff_id: str = Field(default="", max_length=50)
    plaintiff_contact: str = Field(default="", max_length=200)
    defendant_name: str = Field(default="", max_length=200)
    defendant_cr_number: str = Field(default="", max_length=50)
    workplace_location: str = Field(default="", max_length=200)
    job_title: str = Field(default="", max_length=200)
    start_date: str = Field(default="", max_length=10)
    end_date: str = Field(default="", max_length=10)
    dispute_category_key: str = Field(default="dismissal", max_length=50)
    facts: List[AmicableSettlementFactIn] = Field(default_factory=list)
    claims: List[AmicableSettlementClaimIn] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class SettlementOfferReviewRequest(BaseModel):
    offer_text: str = Field(min_length=1, max_length=20000)


class EntitlementsWorksheetRequest(BaseModel):
    basic_salary: float = Field(gt=0)
    total_salary: float = Field(gt=0)
    start_date: str = Field(min_length=8, max_length=10)
    end_date: str = Field(min_length=8, max_length=10)
    termination_type: str = Field(description="'فصل تعسفي' | 'فصل بسبب (م81)' | 'استقالة' | 'انتهاء مدة العقد'")
    notice_given_days: int = Field(default=0, ge=0)
    monthly_paid: bool = True
    unused_leave_days: Optional[float] = Field(default=None, ge=0)
    overtime_hours: float = Field(default=0, ge=0)
    overtime_hourly_rate: Optional[float] = Field(default=None, ge=0)


class RightsAnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000)
    right_concepts: Dict[str, List[str]] = Field(default_factory=dict)
    semantic_matches: List[Dict[str, Any]] = Field(default_factory=list)
    table_entities: List[Dict[str, Any]] = Field(default_factory=list)
    claim_keys: List[str] = Field(default_factory=list)
    right_catalog: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    document_id: Optional[str] = None
    filename: Optional[str] = None
    page: Optional[int] = Field(default=None, ge=1)


class RightReviewRequest(BaseModel):
    discovered_right_id: str = Field(min_length=2, max_length=120)
    decision: str = Field(min_length=2, max_length=100)
    note: str = Field(default="", max_length=2000)


async def require_access(x_app_token: Optional[str] = Header(default=None)) -> None:
    if not APP_TOKEN:
        raise HTTPException(status_code=503, detail="APP_ACCESS_TOKEN غير مضبوط على الخادم")
    if not x_app_token or not hmac.compare_digest(x_app_token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="رمز الوصول غير صحيح")


def selected_preset(name: Optional[str]) -> str:
    # المرحلة صفر: النموذج المحلي (Qwen 0.6B) غير كافٍ لتحليل قانوني جاد ويبقى
    # خيارًا احتياطيًا فقط عبر PRESET_NAME في .env؛ الافتراضي الآن نموذج حقيقي.
    return name or os.getenv("PRESET_NAME", "Claude Sonnet 4 🎯")


def selected_key(preset: str) -> str:
    info = ai_engine.get_preset_info(preset)
    fmt = info.get("fmt")
    if fmt == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY", "")
    if fmt == "huggingface":
        return os.getenv("HF_API_KEY", "")
    return os.getenv("OPENAI_API_KEY", "")


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(os.path.join(WEB_DIR, "templates", "index.html"))


@app.get("/manifest.json", include_in_schema=False)
async def manifest():
    return FileResponse(os.path.join(WEB_DIR, "static", "manifest.json"), media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    return FileResponse(os.path.join(WEB_DIR, "static", "sw.js"), media_type="application/javascript")


@app.get("/health")
async def health():
    return {"ok": True, "app": "Führer PWA", "version": app.version, "single_user": True}


@app.get("/api/dashboard")
async def dashboard(_: None = Depends(require_access)):
    return {"ok": True, "dashboard": workspace_store.dashboard()}


@app.get("/api/matters")
async def matters(status: Optional[str] = None, _: None = Depends(require_access)):
    return {"ok": True, "matters": workspace_store.list_matters(status=status)}


@app.post("/api/matters")
async def create_matter(request: MatterCreateRequest, _: None = Depends(require_access)):
    return {"ok": True, "matter": workspace_store.create_matter(request.model_dump())}


@app.get("/api/matters/{matter_id}")
async def get_matter(matter_id: str, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.get_matter(matter_id)}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.get("/api/roles")
async def roles(_: None = Depends(require_access)):
    return {"ok": True, "roles": advanced_dispute_engine.role_catalog()}


@app.get("/api/matters/{matter_id}/advanced-review")
async def advanced_review(matter_id: str, role: str = "مستشار عمالي", _: None = Depends(require_access)):
    try:
        matter = workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {"ok": True, "review": advanced_dispute_engine.assess_matter(matter, role)}


@app.get("/api/matters/{matter_id}/case-theory")
async def case_theory(matter_id: str, role: str = "مستشار عمالي", _: None = Depends(require_access)):
    try:
        matter = workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {"ok": True, "theory": legal_case_theory.build_case_theory(matter, role)}


@app.patch("/api/matters/{matter_id}/procedure/{step_key}")
async def update_procedure_step(matter_id: str, step_key: str, request: Dict[str, Any], _: None = Depends(require_access)):
    try:
        return {"ok": True, "step": workspace_store.update_procedure_step(matter_id, step_key, request)}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية أو المرحلة الإجرائية غير موجودة")


@app.post("/api/matters/{matter_id}/rights/analyze")
async def analyze_rights(matter_id: str, request: RightsAnalysisRequest, _: None = Depends(require_access)):
    try:
        workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    concepts = request.right_concepts or {"overtime": ["ساعات إضافية", "بعد الدوام"]}
    analysis = fuse_text_with_evidence(
        request.text, concepts, request.semantic_matches, request.table_entities,
        document_id=request.document_id, filename=request.filename, page=request.page,
        right_catalog=request.right_catalog, claim_keys=request.claim_keys,
    )
    persisted_statements = []
    for item in analysis["statements"]:
        persisted_statements.append(legal_repository.save_statement(
            matter_id=matter_id, text=item["text"], speaker=item.get("speaker"),
            polarity=item.get("polarity"), status=item.get("status"),
            negation_cue=item.get("negation_cue"), quoted=item.get("quoted", False),
            document_id=item.get("document_id") or request.document_id,
            page_number=item.get("page") or request.page, start_offset=item.get("start"),
            end_offset=item.get("end"), confidence=item.get("confidence"),
        ))
    persisted_findings = []
    for finding in analysis["findings"]:
        saved = legal_repository.save_right_finding(matter_id=matter_id, finding=finding)
        for trace in finding.get("source_trace", []):
            legal_repository.save_right_trigger(
                discovered_right_id=saved["id"], trigger_type=trace.get("trigger_type", "analysis"),
                excerpt=trace.get("excerpt", "") or "", page_number=trace.get("page"),
                source_quality=trace.get("source_quality"),
            )
        persisted_findings.append(saved)
    return {"ok": True, "analysis": analysis, "persisted": {"statements": persisted_statements, "findings": persisted_findings}}


@app.get("/api/matters/{matter_id}/repository-rights")
async def repository_rights(matter_id: str, _: None = Depends(require_access)):
    try:
        workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {"ok": True, "rights": legal_repository.list_right_findings(matter_id), "decisions": legal_repository.list_review_decisions(matter_id)}


@app.get("/api/matters/{matter_id}/legal-statements")
async def repository_statements(matter_id: str, _: None = Depends(require_access)):
    try:
        workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {"ok": True, "statements": legal_repository.list_statements(matter_id)}


@app.post("/api/matters/{matter_id}/right-review")
async def review_right(matter_id: str, request: RightReviewRequest, _: None = Depends(require_access)):
    try:
        workspace_store.get_matter(matter_id)
        decision = legal_repository.save_review_decision(
            matter_id=matter_id, discovered_right_id=request.discovered_right_id,
            decision=request.decision, note=request.note,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية أو الحق المكتشف غير موجود")
    return {"ok": True, "decision": decision}


@app.get("/api/matters/{matter_id}/intelligence")
async def matter_intelligence_endpoint(matter_id: str, _: None = Depends(require_access)):
    # ← المرحلة 2: أُضيفت طبقة الربط بين المستندات والوقائع المُدخلة يدويًا
    # (document_cross_reference داخل analysis) — إضافية بالكامل، لا تُغيّر
    # أي حقل كان موجودًا في الاستجابة سابقًا.
    try:
        matter = workspace_store.get_matter(matter_id)
        document_texts = workspace_store.get_document_texts(matter_id)
        return {"ok": True, "analysis": intelligence_engine.analyze_matter_deep(matter, document_texts)}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.post("/api/matters/{matter_id}/correspondence")
async def ingest_correspondence(matter_id: str, request: CorrespondenceIngestRequest, _: None = Depends(require_access)):
    """
    ← المرحلة 4. استيعاب مباشر لنص مراسلات جاهز (بريد/واتساب منسوخ أو
    مُصدَّر) دون المرور بـ file_processing.py — لا حاجة لاستخراج OCR لنص
    موجود أصلًا كنص. كل عنصر يُخزَّن كمستند بنوع 'مراسلة' مع بصمة SHA-256
    لنصه، ومتبوعًا بالتاريخ/القناة في metadata إن أُرسلا؛ لا يُشترط اسم أو
    هوية مُرسل (توضيح: المراسلات عبر منصة رسمية موثّقة الهوية أصلًا).
    """
    try:
        workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")

    saved = []
    for item in request.items:
        digest = hashlib.sha256(item.text.encode("utf-8")).hexdigest()
        doc = workspace_store.add_document(
            matter_id=matter_id, filename=f"مراسلة_{digest[:8]}.txt", kind="مراسلة",
            extracted_text=item.text, source_hash=digest, byte_size=len(item.text.encode("utf-8")),
            mime_type="text/plain", metadata={"date": item.date, "channel": item.channel},
        )
        saved.append(doc)
    return {"ok": True, "saved": len(saved), "documents": saved}


@app.get("/api/matters/{matter_id}/correspondence-analysis")
async def correspondence_analysis_endpoint(matter_id: str, _: None = Depends(require_access)):
    try:
        matter = workspace_store.get_matter(matter_id)
        document_texts = workspace_store.get_document_texts(matter_id)
        return {"ok": True, "analysis": intelligence_engine.analyze_correspondence_for_matter(matter, document_texts)}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.get("/api/matters/{matter_id}/package")
async def matter_package(matter_id: str, _: None = Depends(require_access)):
    try:
        package = case_package.build_package(workspace_store.get_matter(matter_id))
        return {"ok": True, "package": package}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.get("/api/matters/{matter_id}/package.html")
async def matter_package_html(matter_id: str, _: None = Depends(require_access)):
    from fastapi.responses import HTMLResponse
    try:
        package = case_package.build_package(workspace_store.get_matter(matter_id))
        return HTMLResponse(case_package.to_html(package))
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.get("/api/matters/{matter_id}/package.md")
async def matter_package_markdown(matter_id: str, _: None = Depends(require_access)):
    try:
        package = case_package.build_package(workspace_store.get_matter(matter_id))
        return {"ok": True, "format": "markdown", "content": case_package.to_markdown(package)}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.get("/api/matters/{matter_id}/report")
async def matter_report(matter_id: str, _: None = Depends(require_access)):
    try:
        matter = workspace_store.get_matter(matter_id)
        return {"ok": True, "matter_id": matter_id, "format": "markdown", "report": reporting.build_matter_report(matter)}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.patch("/api/matters/{matter_id}")
async def update_matter(matter_id: str, request: MatterUpdateRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.update_matter(matter_id, request.model_dump(exclude_none=True))}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.post("/api/matters/{matter_id}/parties")
async def add_party(matter_id: str, request: PartyRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.add_party(matter_id, request.model_dump())}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.post("/api/matters/{matter_id}/facts")
async def add_fact(matter_id: str, request: FactRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.add_fact(matter_id, request.model_dump())}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.post("/api/matters/{matter_id}/claims")
async def add_claim(matter_id: str, request: ClaimRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.add_claim(matter_id, request.model_dump())}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.post("/api/matters/{matter_id}/claim-evidence")
async def link_claim_evidence(matter_id: str, request: ClaimEvidenceRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.link_claim_evidence(matter_id, request.model_dump())}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية أو الطلب أو المستند غير موجود")


@app.post("/api/matters/{matter_id}/deadlines")
async def add_deadline(matter_id: str, request: DeadlineRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.add_deadline(matter_id, request.model_dump())}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.post("/api/matters/{matter_id}/tasks")
async def create_task(matter_id: str, request: TaskRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.create_task(matter_id, request.model_dump())}
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, request: TaskRequest, _: None = Depends(require_access)):
    try:
        return {"ok": True, "matter": workspace_store.update_task(task_id, request.model_dump())}
    except KeyError:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")


@app.get("/api/documents/{document_id}/integrity")
async def document_integrity(document_id: str, matter_id: Optional[str] = None, _: None = Depends(require_access)):
    try:
        return {"ok": True, "integrity": workspace_store.verify_document(document_id, matter_id)}
    except KeyError:
        raise HTTPException(status_code=404, detail="المستند غير موجود")


@app.get("/api/backup")
async def download_backup(_: None = Depends(require_access)):
    archive_path = workspace_store.build_backup_archive()
    return FileResponse(archive_path, media_type="application/zip", filename="fuhrer-backup.zip", background=BackgroundTask(lambda: os.path.exists(archive_path) and os.remove(archive_path)))


@app.get("/api/auth/verify")
async def verify_access(_: None = Depends(require_access)):
    return {"ok": True, "single_user": True}


@app.get("/api/models")
async def models(_: None = Depends(require_access)):
    return ai_engine.get_all_models_grouped()


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest, _: None = Depends(require_access)):
    preset = selected_preset(request.preset_name)
    response = await asyncio.to_thread(
        ai_engine.call_ai,
        prompt=request.prompt,
        history=[],
        system=request.system,
        preset_name=preset,
        api_key=selected_key(preset),
    )
    return {"ok": True, "response": response, "preset": preset}


@app.post("/api/law-search")
async def law_search(request: SearchRequest, _: None = Depends(require_access)):
    return {"ok": True, "results": search_with_sources(request.query, request.max_results)}


@app.get("/api/procedure/{step_key}/requirements")
async def procedure_requirements_endpoint(step_key: str, _: None = Depends(require_access)):
    return {"ok": True, "requirements": procedure_requirements(step_key)}


@app.get("/api/legal/sources")
async def legal_sources(_: None = Depends(require_access)):
    return {"ok": True, "sources": OFFICIAL_SOURCES}


@app.post("/api/legal/review")
async def legal_review(request: ClaimAmountTextRequest, _: None = Depends(require_access)):
    return {"ok": True, "review": legal_review_package(request.text, request.claim_amount)}


@app.post("/api/legal/obligations")
async def legal_obligations(request: TextRequest, _: None = Depends(require_access)):
    return {"ok": True, "obligations": extract_obligations(request.text)}


@app.post("/api/legal/risks")
async def legal_risks(request: TextRequest, _: None = Depends(require_access)):
    return {"ok": True, "risks": scan_risks(request.text)}


@app.post("/api/legal/evidence")
async def legal_evidence(request: TextRequest, _: None = Depends(require_access)):
    return {"ok": True, "checklist": evidence_checklist(request.text)}


@app.post("/api/classify")
async def classify(text: str, _: None = Depends(require_access)):
    return {"ok": True, "result": legal_classifier.classify(text)}


@app.post("/api/legal/extract-info")
async def extract_info(request: TextRequest, _: None = Depends(require_access)):
    return {"ok": True, "extracted": info_extractor.extract_all(request.text)}


@app.post("/api/legal/evidence-score")
async def evidence_score(request: EvidenceScoreRequest, _: None = Depends(require_access)):
    return {"ok": True, "score": evidence_scorer.score([item.model_dump() for item in request.evidence])}


@app.get("/api/legal/evidence-gaps/{case_type}")
async def evidence_gaps(case_type: str, _: None = Depends(require_access)):
    return {"ok": True, "case_type": case_type, "required_evidence": evidence_scorer.gaps_for(case_type)}


@app.post("/api/legal/entitlements/severance")
async def entitlement_severance(request: SeveranceRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": entitlement_calculator.severance_pay(request.basic_salary, request.years_of_service, request.resignation)}


@app.post("/api/legal/entitlements/arbitrary-dismissal-floor")
async def entitlement_arbitrary_dismissal(request: ArbitraryDismissalRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": entitlement_calculator.arbitrary_dismissal_floor(request.total_salary, request.years_of_service)}


@app.post("/api/legal/entitlements/wage-delay-rights")
async def entitlement_wage_delay(request: WageDelayRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": entitlement_calculator.wage_delay_rights(request.days_delayed)}


@app.post("/api/legal/entitlements/overtime")
async def entitlement_overtime(request: OvertimeRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": entitlement_calculator.overtime_pay(request.hourly_rate, request.overtime_hours)}


@app.post("/api/legal/entitlements/annual-leave")
async def entitlement_annual_leave(request: AnnualLeaveRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": entitlement_calculator.annual_leave_balance(request.start_date, request.end_date)}


@app.post("/api/legal/lawsuit-draft")
async def lawsuit_draft(request: LawsuitDraftRequest, _: None = Depends(require_access)):
    return {"ok": True, "draft": lawsuit_drafter.draft(request.model_dump())}


@app.get("/api/legal/litigation-timeline")
async def litigation_timeline_endpoint(_: None = Depends(require_access)):
    return {"ok": True, "timeline": litigation_timeline.timeline()}


# ← المرحلة 3: محركات المواعيد/التقادم، مشروعية الإنهاء، وورقة العمل الشاملة
@app.post("/api/legal/deadlines/prescription")
async def prescription_endpoint(request: PrescriptionRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": deadline_engine.prescription_deadline(request.reference_date, request.claim_type)}


@app.post("/api/legal/deadlines/all")
async def all_deadlines_endpoint(request: AllDeadlinesRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": deadline_engine.all_deadlines(request.termination_date, request.claim_type, request.notice_given_days, request.monthly_paid)}


@app.post("/api/legal/termination-assessment")
async def termination_assessment_endpoint(request: TerminationAssessmentRequest, _: None = Depends(require_access)):
    result = termination_assessment.assess(request.initiated_by, request.notice_given_days, request.monthly_paid, request.employer_claimed_ground, request.worker_claimed_ground)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"ok": True, "result": result}


@app.post("/api/legal/entitlements/full-worksheet")
async def full_worksheet_endpoint(request: EntitlementsWorksheetRequest, _: None = Depends(require_access)):
    result = full_entitlements_worksheet(
        request.basic_salary, request.total_salary, request.start_date, request.end_date,
        request.termination_type, request.notice_given_days, request.monthly_paid,
        request.unused_leave_days, request.overtime_hours, request.overtime_hourly_rate,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"ok": True, "result": result}


# ← المرحلة 5: صياغة طلب التسوية الودية (منصة تراضي) وفحص عروض التسوية
@app.get("/api/legal/amicable-settlement/categories")
async def amicable_settlement_categories(_: None = Depends(require_access)):
    return {"ok": True, "categories": DISPUTE_SUBJECT_CATEGORIES}


@app.post("/api/legal/amicable-settlement/draft")
async def amicable_settlement_draft_standalone(request: AmicableSettlementDraftRequest, _: None = Depends(require_access)):
    result = amicable_drafter.draft(
        plaintiff_name=request.plaintiff_name, plaintiff_id=request.plaintiff_id, plaintiff_contact=request.plaintiff_contact,
        defendant_name=request.defendant_name, defendant_cr_number=request.defendant_cr_number,
        workplace_location=request.workplace_location, job_title=request.job_title,
        start_date=request.start_date, end_date=request.end_date, dispute_category_key=request.dispute_category_key,
        facts=[f.model_dump() for f in request.facts], claims=[c.model_dump() for c in request.claims], evidence=request.evidence,
    )
    return {"ok": True, "result": result}


@app.post("/api/matters/{matter_id}/amicable-settlement/draft")
async def amicable_settlement_draft_from_matter(matter_id: str, dispute_category_key: str = "dismissal", plaintiff_contact: str = "", _: None = Depends(require_access)):
    try:
        matter = workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {"ok": True, "result": intelligence_engine.draft_amicable_settlement_for_matter(matter, dispute_category_key, plaintiff_contact)}


@app.post("/api/legal/settlement-offer-review")
async def settlement_offer_review_endpoint(request: SettlementOfferReviewRequest, _: None = Depends(require_access)):
    return {"ok": True, "result": settlement_reviewer.review(request.offer_text)}


@app.get("/api/legal/settlement-checklist")
async def settlement_checklist_endpoint(_: None = Depends(require_access)):
    return {"ok": True, "checklist": pre_signature_checklist()}


@app.get("/api/matters/{matter_id}/document-inspections")
async def document_inspections(matter_id: str, _: None = Depends(require_access)):
    try:
        matter = workspace_store.get_matter(matter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    objects = []
    for document in matter.get("documents", []):
        path = document.get("storage_path")
        if not path or not os.path.isfile(path):
            continue
        with open(path, "rb") as blob:
            item = io.BytesIO(blob.read())
        item.name = document.get("filename", "document")
        objects.append(item)
    batch = document_inspection_engine.inspect_batch(objects)
    return {"ok": True, "coverage": {key: batch.get(key) for key in ("documents_total", "documents_read", "documents_partial", "documents_unreadable", "documents_fully_inspected", "characters_scanned", "pages_scanned", "unsupported_extensions", "manual_review_required", "status")}, "inspections": batch.get("results", [])}


@app.get("/api/matters/{matter_id}/discovered-rights")
async def discovered_rights(matter_id: str, _: None = Depends(require_access)):
    try:
        matter = workspace_store.get_matter(matter_id)
        texts = workspace_store.get_document_texts(matter_id)
        for document in matter.get("documents", []):
            document["extracted_text"] = texts.get(document.get("id"), "")
    except KeyError:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {"ok": True, "rights": hidden_rights_engine.discover(matter).get("findings", [])}


@app.post("/api/upload")
async def upload(files: List[UploadFile] = File(...), matter_id: Optional[str] = Form(default=None), _: None = Depends(require_access)):
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=413, detail=f"الحد الأقصى {MAX_FILES} ملفات")
    file_objects = []
    file_metadata = {}
    for upload in files:
        data = await upload.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail=f"الملف {upload.filename} يتجاوز الحد المسموح")
        if not upload.filename:
            raise HTTPException(status_code=400, detail="اسم ملف غير صالح")
        file_obj = io.BytesIO(data)
        file_obj.name = upload.filename
        file_objects.append(file_obj)
        file_metadata[upload.filename] = {"mime_type": upload.content_type or "application/octet-stream", "byte_size": len(data)}
    batch = file_processing.process_multiple_files(file_objects)
    saved_documents = []
    saved_inspections = []
    rights_discovery = {"findings": [], "undisclosed_count": 0}
    if matter_id:
        try:
            for item in batch.get("results", []):
                if item.get("success"):
                    text = item.get("text", "")
                    filename = item.get("filename", "مستند")
                    original = next((obj for obj in file_objects if getattr(obj, "name", "") == filename), None)
                    raw_bytes = original.getvalue() if original is not None else text.encode("utf-8")
                    metadata = file_metadata.get(filename, {})
                    saved_documents.append(workspace_store.add_document(matter_id, filename, "مرفوع", text, hashlib.sha256(raw_bytes).hexdigest(), byte_size=metadata.get("byte_size", len(raw_bytes)), mime_type=metadata.get("mime_type", "application/octet-stream"), metadata=item.get("signals", {}), raw_bytes=raw_bytes))
            inspection_objects = []
            for source in file_objects:
                inspection = io.BytesIO(source.getvalue())
                inspection.name = getattr(source, "name", "document")
                inspection_objects.append(inspection)
            inspected = document_inspection_engine.inspect_batch(inspection_objects)
            saved_inspections = inspected.get("results", [])
            analyzed_matter = workspace_store.get_matter(matter_id)
            texts = workspace_store.get_document_texts(matter_id)
            for document in analyzed_matter.get("documents", []):
                document["extracted_text"] = texts.get(document.get("id"), "")
            rights_discovery = hidden_rights_engine.discover(analyzed_matter)
        except KeyError:
            raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {
        "ok": True,
        "summary": {"total": batch["total"], "success": batch["success"], "failed": batch["failed"]},
        "results": batch["results"],
        "texts": batch["texts"],
        "saved_documents": saved_documents,
        "saved_inspections": saved_inspections,
        "inspection_coverage": {key: value for key, value in batch.items() if key in {"documents_total", "documents_read", "documents_partial", "documents_unreadable", "documents_fully_inspected", "characters_scanned", "pages_scanned", "unsupported_extensions", "manual_review_required", "status"}},
        "rights_discovery": rights_discovery,
    }
