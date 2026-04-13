import sqlite3
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv
import logging
import mysql.connector
from mysql.connector import Error

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_website_content(db_path):
    """Fetch scraped content from SQLite db."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT url, title, content FROM pages")
    rows = c.fetchall()
    conn.close()
    return rows

def fetch_sql_data():
    """Fetch help support data from SQL db specified in .env."""
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = int(os.getenv('DB_PORT', '11111'))
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME')
    table_name = os.getenv('TABLE_NAME')
    
    if not all([host, user, password, database, table_name]):
        logger.warning("SQL DB credentials incomplete in .env. Skipping SQL data.")
        return []
    
    # Use description and resolution columns as requested
    query = f"""
    SELECT description, resolution 
    FROM `{table_name}` 
    WHERE description IS NOT NULL 
    AND resolution IS NOT NULL 
    AND TRIM(description) != '' 
    AND TRIM(resolution) != ''
    """
    
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            auth_plugin='mysql_native_password',
        )
        logger.info(f"Connected to SQL DB: {database}")
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Fetched {len(rows)} records from {table_name}")
            return rows
    except Error as e:
        logger.error(f"SQL Error: {e}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def chunk_text(text, chunk_size=2000, overlap=200):
    """Simple chunking logic for large chunks."""
    chunks = []
    if len(text) <= chunk_size:
        return [text]
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

def main():
    load_dotenv()
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "website_data.db"
    faq_file = base_dir / "fyjc_faq_full.txt"
    index_path = base_dir / "faiss_index.bin"
    matrix_path = base_dir / "embed_matrix.npy"

    all_documents = []

    # 1. Load original FAQs
    if faq_file.exists():
        logger.info("Loading existing FAQs...")
        with open(faq_file, "r", encoding="utf-8") as f:
            all_documents.extend([line.strip() for line in f if line.strip()])

    # 2. Load and chunk website content
    if db_path.exists():
        pages = get_website_content(db_path)
        for url, title, content in pages:
            logger.info(f"Processing website page: {url}")
            prefix = f"Source: {url} | Title: {title}\n"
            chunks = chunk_text(content, chunk_size=1500)
            for chunk in chunks:
                all_documents.append(prefix + chunk)
    else:
        logger.warning(f"Website database not found: {db_path}")

    # 3. Load SQL DB data (Help Support)
    sql_records = fetch_sql_data()
    for row in sql_records:
        q = row['description'].strip()
        a = row['resolution'].strip()
        # Format as Q&A pair
        doc = f"Support Query: {q}\nResolution: {a}"
        # If long, chunk it, but usually support tickets are short
        if len(doc) > 2000:
            chunks = chunk_text(doc, chunk_size=1500)
            all_documents.extend(chunks)
        else:
            all_documents.append(doc)

    if not all_documents:
        logger.error("No documents found to ingest!")
        return

    logger.info(f"Total documents to embed: {len(all_documents)}")

    # 4. Embed and build index
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    embedder = SentenceTransformer(model_name)
    
    logger.info("Embedding texts... this may take a moment.")
    matrix = embedder.encode(all_documents, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    
    dim = matrix.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(matrix)
    
    # 5. Save
    faiss.write_index(index, str(index_path))
    np.save(matrix_path, matrix)
    
    with open(base_dir / "knowledge_base.txt", "w", encoding="utf-8") as f:
        for doc in all_documents:
            # For lookup, we keep it as one line but preserve context
            f.write(doc.replace("\n", " [BREAK] ") + "\n")
            
    logger.info(f"Saved index: {index_path}, matrix: {matrix_path}, unified knowledge: knowledge_base.txt")

if __name__ == "__main__":
    main()
