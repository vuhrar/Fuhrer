import os
from app.rag import RAGStore

# Simple script to build FAISS index from law_text.txt or law_knowledge_base.json
SOURCE_TXT = os.getenv("LAW_TEXT_PATH", "law_text.txt")
INDEX_DIR = os.getenv("FAISS_INDEX_PATH", "./faiss_index")

if not os.path.exists(SOURCE_TXT):
    print(f"Source file not found: {SOURCE_TXT}\nPlace your law_text.txt in the project root or set LAW_TEXT_PATH env var.")
    exit(1)

with open(SOURCE_TXT, "r", encoding="utf-8") as f:
    txt = f.read()

# split into chunks of approximately chunk_size characters
chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
chunks = [txt[i:i+chunk_size].strip() for i in range(0, len(txt), chunk_size) if txt[i:i+chunk_size].strip()]

print(f"Building FAISS index with {len(chunks)} chunks (chunk_size={chunk_size})...")

r = RAGStore(index_dir=INDEX_DIR)
r.build(chunks)

print("FAISS index built at:", INDEX_DIR)
