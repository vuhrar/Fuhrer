"""Führer PWA API: المسار التشغيلي الوحيد للتطبيق."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import io
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

import ai_engine
import file_processing
import workspace_store
import reporting
import case_package
from legal_tools_advanced import legal_classifier
from legal_intelligence import OFFICIAL_SOURCES, evidence_checklist, extract_obligations, legal_review_package, scan_risks, search_with_sources

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
APP_TOKEN = os.getenv("APP_ACCESS_TOKEN", "").strip()
MAX_FILES = int(os.getenv("MAX_FILES", "5"))
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", str(25 * 1024 * 1024)))

app = FastAPI(title="Führer Personal Legal PWA", version="3.0.0", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(WEB_DIR, "static")), name="static")


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


async def require_access(x_app_token: Optional[str] = Header(default=None)) -> None:
    if not APP_TOKEN:
        raise HTTPException(status_code=503, detail="APP_ACCESS_TOKEN غير مضبوط على الخادم")
    if not x_app_token or not hmac.compare_digest(x_app_token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="رمز الوصول غير صحيح")


def selected_preset(name: Optional[str]) -> str:
    return name or os.getenv("PRESET_NAME", "Führer Law Brain (Qwen 0.6B) 🧠")


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


@app.post("/api/auth/verify")
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


@app.get("/api/legal/sources")
async def legal_sources(_: None = Depends(require_access)):
    return {"ok": True, "sources": OFFICIAL_SOURCES}


@app.post("/api/legal/review")
async def legal_review(request: TextRequest, _: None = Depends(require_access)):
    return {"ok": True, "review": legal_review_package(request.text)}


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


@app.post("/api/upload")
async def upload(files: List[UploadFile] = File(...), matter_id: Optional[str] = Form(default=None), _: None = Depends(require_access)):
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=413, detail=f"الحد الأقصى {MAX_FILES} ملفات")
    file_objects = []
    for upload in files:
        data = await upload.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail=f"الملف {upload.filename} يتجاوز الحد المسموح")
        if not upload.filename:
            raise HTTPException(status_code=400, detail="اسم ملف غير صالح")
        file_obj = io.BytesIO(data)
        file_obj.name = upload.filename
        file_objects.append(file_obj)
    batch = file_processing.process_multiple_files(file_objects)
    saved_documents = []
    if matter_id:
        try:
            for item in batch.get("results", []):
                if item.get("success"):
                    text = item.get("text", "")
                    saved_documents.append(workspace_store.add_document(matter_id, item.get("filename", "مستند"), "مرفوع", text, hashlib.sha256(text.encode("utf-8")).hexdigest()))
        except KeyError:
            raise HTTPException(status_code=404, detail="القضية غير موجودة")
    return {
        "ok": True,
        "summary": {"total": batch["total"], "success": batch["success"], "failed": batch["failed"]},
        "results": batch["results"],
        "texts": batch["texts"],
        "saved_documents": saved_documents,
    }
