from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import os

from app.ai_adapter import LocalLLM
from app.rag import RAGStore

# storage and analysis
import storage
import analysis_engine

MODEL_PATH = os.getenv("GGUF_MODEL_PATH", "./models/DeepSeek-R1-Distill-Qwen-1.5B-abliterated.Q4_K_S.gguf")
EMBED_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")

app = FastAPI(title="Fuhrer Local API")

# محرك LLM (حمل مرة واحدة)
llm = LocalLLM()
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
            if hits:
                context = "\n\n".join([f"[المصدر {i+1}] {h['text']}" for i, h in enumerate(hits)])
        prompt_with_context = (req.system + "\n\n" if req.system else "") + (context + "\n\n" if context else "") + req.prompt
        out = llm.generate(prompt_with_context, temperature=req.temperature, max_tokens=req.max_tokens, top_k=req.top_k)
        return {"ok": True, "result": out, "context_snippets": hits if req.use_rag else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AnalysisRequest(BaseModel):
    case_text: str
    use_rag: bool = True
    rag_k: int = 5
    background: bool = True


def _call_fn(prompt, history, system):
    # wrapper expected by analysis_engine: (prompt, history, system) -> str
    system_pref = (system + "\n\n") if system else ""
    return llm.generate(system_pref + prompt, temperature=0.1, max_tokens=512)


def _run_and_save_analysis(case_text: str):
    try:
        res = analysis_engine.run_full_analysis(case_text, _call_fn)
        # save as a case
        cid = storage.create_case({
            "title": f"تحليل قضية {case_text[:30]}...",
            "description": case_text,
            "persona": "lawyer",
        })
        case_data = storage.load_case(cid)
        case_data["analysis"] = res
        storage.save_case(cid, case_data)
    except Exception as e:
        # log to file
        with open("./analysis_errors.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")


@app.post("/api/analysis")
def analysis(req: AnalysisRequest, background_tasks: BackgroundTasks):
    if req.background:
        background_tasks.add_task(_run_and_save_analysis, req.case_text)
        return {"ok": True, "message": "analysis started in background"}
    else:
        try:
            res = analysis_engine.run_full_analysis(req.case_text, _call_fn)
            return {"ok": True, "result": res}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# include storage router (sessions / cases)
from app.storage_api import router as storage_router
app.include_router(storage_router, prefix="/api")
