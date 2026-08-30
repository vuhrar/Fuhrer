"""Führer PWA API: المسار التشغيلي الوحيد للتطبيق."""
from __future__ import annotations

import asyncio
import hmac
import io
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

import ai_engine
import file_processing
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
async def upload(files: List[UploadFile] = File(...), _: None = Depends(require_access)):
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
    return {
        "ok": True,
        "summary": {"total": batch["total"], "success": batch["success"], "failed": batch["failed"]},
        "results": batch["results"],
        "texts": batch["texts"],
    }
