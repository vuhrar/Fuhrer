from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
from app.ai_adapter import LocalLLM
from app.rag import RAGStore

MODEL_PATH = os.getenv("GGUF_MODEL_PATH", "./models/DeepSeek-R1-Distill-Qwen-1.5B-abliterated.Q4_K_S.gguf")
EMBED_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")

app = FastAPI(title="Fuhrer Local API")

# محرك LLM (حمل مرة واحدة)
llm = LocalLLM(model_path=MODEL_PATH)
rag = RAGStore(index_dir=EMBED_INDEX_PATH)

class AICallReq(BaseModel):
    prompt: str
    temperature: float = 0.1
    max_tokens: int = 512
    top_k: int = 50
    use_rag: bool = True
    rag_k: int = 5
    system: Optional[str] = None
    preset: Optional[str] = None

@app.post("/api/ai_call")
def ai_call(req: AICallReq):
    try:
        context = ""
        hits = []
        if req.use_rag:
            hits = rag.search(req.prompt, top_k=req.rag_k)
            # أبني سياق بسيط من النتائج
            if hits:
                context = "\n\n".join([f"[المصدر {i+1}] {h['text']}" for i, h in enumerate(hits)])
        prompt_with_context = (req.system + "\n\n" if req.system else "") + (context + "\n\n" if context else "") + req.prompt
        out = llm.generate(prompt_with_context, temperature=req.temperature, max_tokens=req.max_tokens, top_k=req.top_k)
        return {"ok": True, "result": out, "context_snippets": hits if req.use_rag else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_law")
def upload_law(file: UploadFile = File(...)):
    # تحميل ملف نصي لتضمينه بالـ RAG indexing لاحقاً
    target = "./uploads"
    os.makedirs(target, exist_ok=True)
    path = os.path.join(target, file.filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {"ok": True, "path": path}
