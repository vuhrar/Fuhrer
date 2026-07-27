import os
import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

EMB_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

class RAGStore:
    def __init__(self, index_dir: str = "./faiss_index"):
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        self.emb = SentenceTransformer(EMB_MODEL)
        self.index_path = os.path.join(index_dir, "index.faiss")
        self.meta_path = os.path.join(index_dir, "meta.json")
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
            except Exception:
                self.index = None
                self.meta = []
        else:
            self.index = None
            self.meta = []

    def build(self, texts: list):
        if not texts:
            raise ValueError("No texts provided to build index")
        vecs = self.emb.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        # use inner product on L2-normalized vectors
        d = vecs.shape[1]
        index = faiss.IndexFlatIP(d)
        faiss.normalize_L2(vecs)
        index.add(vecs)
        faiss.write_index(index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump([{"text": t} for t in texts], f, ensure_ascii=False, indent=2)
        self.index = index
        self.meta = [{"text": t} for t in texts]

    def search(self, query: str, top_k: int = 5):
        if self.index is None:
            return []
        qv = self.emb.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(qv)
        scores, idxs = self.index.search(qv, top_k)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(self.meta):
                continue
            results.append({"score": float(score), "text": self.meta[idx]["text"]})
        return results
