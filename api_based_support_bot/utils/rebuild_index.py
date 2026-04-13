import os
import numpy as np
import faiss
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load env to get embedding model name
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
KB_FILE = BASE_DIR / "knowledge_base.txt"
INDEX_PATH = BASE_DIR / "faiss_index.bin"
MATRIX_PATH = BASE_DIR / "embed_matrix.npy"

def rebuild():
    print(f"Loading knowledge_base.txt from {KB_FILE}...")
    if not KB_FILE.exists():
        print(f"Error: {KB_FILE} not found.")
        return

    with open(KB_FILE, "r", encoding="utf-8") as f:
        # Load entries and restore newlines from [BREAK]
        entries = [line.replace(" [BREAK] ", "\n").strip() for line in f if line.strip()]

    print(f"Loaded {len(entries)} entries.")

    print(f"Loading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # E5-specific: use 'passage: ' prefix for documents
    print("Encoding entries with 'passage: ' prefix...")
    # Use 'passage: ' prefix for e5-base
    prefixed_entries = [f"passage: {e}" for e in entries]
    
    # Encode
    matrix = model.encode(prefixed_entries, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)
    matrix = matrix.astype("float32")

    print(f"Building FAISS index (dimension: {matrix.shape[1]})...")
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)

    print(f"Saving artifacts to {INDEX_PATH} and {MATRIX_PATH}...")
    faiss.write_index(index, str(INDEX_PATH))
    np.save(MATRIX_PATH, matrix)

    print(f"✅ Success! Rebuilt index with {index.ntotal} vectors.")

if __name__ == "__main__":
    rebuild()
