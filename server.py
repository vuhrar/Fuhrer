"""server.py
واجهة HTTP صغيرة باستخدام FastAPI تتيح استدعاء وظائف المعالجة وتحليل النصوص عبر ai_engine.
"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import io
import os
from dotenv import load_dotenv

load_dotenv()

import ai_engine
import file_processing

app = FastAPI(title="Führer API")

# تمكين CORS مبدئيًا للسماح بالوصول من الهاتف/الويب أثناء التطوير
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FileLike(io.BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


@app.get("/health")
async def health():
    return {"ok": True, "message": "Führer API is running"}


@app.get("/models")
async def models():
    return ai_engine.get_all_models_grouped()


@app.post("/analyze")
async def analyze(
    prompt: str = Form(...),
    preset_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    system: Optional[str] = Form("")
):
    preset = preset_name or os.environ.get("PRESET_NAME", "Führer Law Brain (Qwen 0.6B) 🧠")
    api_key_final = api_key or os.environ.get("OPENAI_API_KEY", "")
    # ai_engine.call_ai متزامنة لذلك نستدعيها مباشرة
    try:
        resp = ai_engine.call_ai(prompt=prompt, history=[], system=system, preset_name=preset, api_key=api_key_final)
        return {"ok": True, "response": resp}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.post("/upload")
async def upload(files: List[UploadFile] = File(...), analyze: Optional[bool] = Form(False), preset_name: Optional[str] = Form(None), api_key: Optional[str] = Form(None)):
    """رفع ملفات متعددة ومعالجتها، ثم استدعاء النموذج إن طُلب"""
    file_objs = []
    for upload in files:
        data = await upload.read()
        file_objs.append(FileLike(data, upload.filename))

    batch = file_processing.process_multiple_files(file_objs)

    result = {"ok": True, "summary": {"total": batch["total"], "success": batch["success"], "failed": batch["failed"]}, "results": batch["results"]}

    if analyze and batch["success"] > 0:
        docs_text = batch["texts"]
        prompt = "\n\n---\n".join(docs_text)
        preset = preset_name or os.environ.get("PRESET_NAME", "Führer Law Brain (Qwen 0.6B) 🧠")
        api_key_final = api_key or os.environ.get("OPENAI_API_KEY", "")
        resp = ai_engine.call_ai(prompt=prompt, history=[], system="", preset_name=preset, api_key=api_key_final)
        result["ai_response"] = resp

    return result
