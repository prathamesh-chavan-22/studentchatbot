import os
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from loguru import logger
from pathlib import Path

def load_faq(file_path):
    """Parse the FAQ file into Q&A pairs."""
    qa_pairs = []
    if not os.path.exists(file_path):
        return []
    
    current_q = ""
    current_a = ""
    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.lower().startswith("fyjc faqs") or line.lower().startswith("source:"):
                continue
            
            # Match question patterns like "प्र. 1" or lines ending in "?"
            if re.match(r"प्र\.\s*\d+", line) or line.startswith("Q:") or line.endswith("?"):
                if current_q:
                    qa_pairs.append(f"Q: {current_q.strip()}\nA: {current_a.strip()}")
                current_q = line.replace("Q:", "").strip()
                current_a = ""
            else:
                current_a += line + " "
        
        if current_q:
            qa_pairs.append(f"Q: {current_q.strip()}\nA: {current_a.strip()}")
            
    return qa_pairs

def load_refined(file_path):
    """Load refined grievances from the text file."""
    if not os.path.exists(file_path):
        return []
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split by the separator used in cluster_and_refine.py
    blocks = content.split("\n\n---\n\n")
    return [b.strip() for b in blocks if b.strip()]

def load_existing_knowledge(file_path):
    """Load existing knowledge from knowledge_base.txt, skipping old FAQ/Grievances if identified."""
    if not os.path.exists(file_path):
        return []
    
    knowledge = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Logic to skip lines that look like they'll be replaced by new FAQ/Grievances
            # For now, let's keep everything that doesn't start with "Q: " (assuming those come from FAQs)
            # or keep everything and deduplicate later by embedding distance (advanced) or exact match.
            knowledge.append(line.replace(" [BREAK] ", "\n"))
    return knowledge

def main():
    load_dotenv()
    
    base_dir = Path(__file__).parent
    faq_file = base_dir / "fyjc_faq_full.txt"
    refined_file = base_dir / "refined_grievances.txt"
    knowledge_file = base_dir / "knowledge_base.txt"
    
    logger.info("Loading FAQ, refined grievances, and existing knowledge...")
    faq_data = load_faq(faq_file)
    refined_data = load_refined(refined_file)
    existing_knowledge = load_existing_knowledge(knowledge_file)
    
    # Simple deduplication based on exact string match
    seen = set()
    unified_knowledge = []
    
    def add_unique(data_list):
        for item in data_list:
            if item.strip() not in seen:
                unified_knowledge.append(item.strip())
                seen.add(item.strip())
    
    add_unique(faq_data)
    add_unique(refined_data)
    add_unique(existing_knowledge)
    
    logger.info(f"Unified into {len(unified_knowledge)} unique knowledge items.")
    
    # Save unified knowledge base
    with open(knowledge_file, "w", encoding="utf-8") as f:
        for item in unified_knowledge:
            flattened = item.replace("\n", " [BREAK] ")
            f.write(flattened + "\n")
            
    logger.success(f"Unified knowledge base saved to {knowledge_file}")
    
    # Embedding and Indexing
    model_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # E5 models require 'passage: ' prefix for documents
    if "e5" in model_name.lower():
        logger.info("Adding 'passage: ' prefix for E5 model compatibility.")
        prefixed_knowledge = [f"passage: {item}" for item in unified_knowledge]
    else:
        prefixed_knowledge = unified_knowledge
        
    logger.info(f"Embedding {len(unified_knowledge)} documents...")
    embeddings = model.encode(prefixed_knowledge, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings).astype("float32")
    
    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    
    # Save
    index_path = base_dir / "faiss_index.bin"
    matrix_path = base_dir / "embed_matrix.npy"
    
    faiss.write_index(index, str(index_path))
    np.save(matrix_path, embeddings)
    
    logger.success(f"FAISS index and matrix saved. Total documents: {len(unified_knowledge)}")

if __name__ == "__main__":
    main()
