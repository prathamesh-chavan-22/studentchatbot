"""
Fix knowledge_base.txt:
1. Replace truncated Q10 quota answer with the full answer
2. Add English FAQ entries (for English queries like "What is FYJC?")
3. Rebuild FAISS index
"""

import os
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
KB_FILE = BASE_DIR / "knowledge_base.txt"
INDEX_PATH = BASE_DIR / "faiss_index.bin"
MATRIX_PATH = BASE_DIR / "embed_matrix.npy"

# ── 1. Full correct answers ─────────────────────────────────────────────────

TRUNCATED_MARKER = "(Full extraction truncated for brevity; all 48+ Q&A pairs from HTML added similarly.)"

FULL_QUOTA_MARATHI = "इन-हाऊस कोटा (१०%), व्यवस्थापन कोटा (५%), अल्पसंख्याक कोटा (५०%) केवळ अल्पसंख्याक विद्यालयांमध्ये."

# English FAQ entries to add (covering failed test cases)
ENGLISH_FAQS = [
    # Q1 - What is FYJC
    "Q: What is FYJC? What does FYJC mean? [BREAK] A: FYJC stands for First Year Junior College. It refers to Class 11 (Std. 11th). The FYJC online admission process is the centralised online system for students who want to take admission to Class 11 in Maharashtra State Board affiliated junior colleges. The official portal is https://mahafyjcadmissions.in",

    # Q2 - Who can apply
    "Q: Who can apply for FYJC admission? Who is eligible for 11th admission? [BREAK] A: Students who have passed Class 10 from any recognised board and wish to take admission to Class 11 in a Maharashtra State Board affiliated junior college can apply for FYJC admission.",

    # Q3 - Is online registration compulsory
    "Q: Is online registration compulsory for FYJC? Is offline application accepted? [BREAK] A: Yes, online registration is mandatory. Offline applications will not be accepted.",

    # Q4 - How to register
    "Q: How to do online registration for FYJC? How to get Login ID and password? How to register on the portal? [BREAK] A: Visit https://mahafyjcadmissions.in and click on 'Student Registration'. Fill in the required details and create a password. You will receive your Login ID via SMS. Keep a note of your security question and password. Take a printout and keep it safe.",

    # Q5 - Can I edit after submission
    "Q: Can I edit my FYJC form after submission? Can I make changes after locking? How to unlock the form? [BREAK] A: Yes, you can make corrections before verification using the 'Unlock Form' option, or by contacting the guidance centre. Use Unlock Form before your application is verified by the school.",

    # Q6 - How many colleges
    "Q: How many colleges can I list in my preferences? What is the maximum number of college preferences? [BREAK] A: A student can list a minimum of 1 and a maximum of 10 junior colleges in their preference order.",

    # Q7 - Documents required
    "Q: What documents are required for FYJC admission? What documents are needed for registration? [BREAK] A: The required documents are: 10th marksheet (Class 10 mark sheet), School Leaving Certificate, and certificates for reservation/special category as mentioned in the admission information booklet (Chapter 6).",

    # Q8 - Other board students
    "Q: I am from another board, can I apply for FYJC? What should other board students do? [BREAK] A: Yes, students from other boards can apply online normally. Fill in your Class 10 marks carefully, lock and verify your application. If your marksheet shows only grades, convert them to marks with the help of your school or a guidance centre. You can find a nearby centre on the portal.",

    # Q9 - ATKT
    "Q: What is ATKT? Who is eligible for ATKT concession in FYJC? When can ATKT students apply? [BREAK] A: ATKT (Allowed to Keep Terms) is a concession by the Maharashtra government for State Board students who failed in 1 or 2 subjects in Class 10. These students are given provisional admission to Class 11 until they clear the subjects. ATKT students can apply after the July supplementary exam results (typically after Special Round 1). This concession is only for Maharashtra State Board students. Students wanting Science stream with ATKT must have at least 40% marks in Science subjects in Class 10.",

    # Q10 - Quota types
    "Q: What are the quota types in FYJC? What is In-house quota, Management quota, Minority quota? [BREAK] A: The quota types in FYJC admission are: In-house quota (10%), Management quota (5%), Minority quota (50% - only in minority colleges/institutions).",

    # College preference count (English variant)
    "Q: What is the minimum and maximum number of college preferences I can give in FYJC? [BREAK] A: You can give a minimum of 1 and a maximum of 10 college preferences.",

    # Quota types English variant
    "Q: Tell me about quotas in FYJC admission. What types of quotas are available? [BREAK] A: FYJC admissions have three quota types: (1) In-house quota - 10% seats reserved for students from the same school attached to the junior college. (2) Management quota - 5% seats managed by the college management. (3) Minority quota - 50% seats in minority institutions reserved for students from that linguistic or religious minority community.",
]

# ── 2. Fix the knowledge_base.txt ──────────────────────────────────────────

print("Reading knowledge_base.txt ...")
with open(KB_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

fixed = 0
new_lines = []
for line in lines:
    if TRUNCATED_MARKER in line:
        # Fix Q10 answer: replace truncated part with full answer
        fixed_line = line.replace(TRUNCATED_MARKER, FULL_QUOTA_MARATHI)
        new_lines.append(fixed_line)
        fixed += 1
        print(f"  ✅ Fixed truncated line: {line[:80].strip()}")
    else:
        new_lines.append(line)

print(f"\nFixed {fixed} truncated lines.")

# Add English FAQ entries at the top (line 0) for high retrieval priority
print(f"\nAdding {len(ENGLISH_FAQS)} English FAQ entries ...")
english_block = [faq + "\n" for faq in ENGLISH_FAQS]
new_lines = english_block + new_lines

with open(KB_FILE, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"knowledge_base.txt updated. New line count: {len(new_lines)}")

# ── 3. Rebuild FAISS index ─────────────────────────────────────────────────

print("\nLoading knowledge_base.txt for indexing ...")
with open(KB_FILE, "r", encoding="utf-8") as f:
    questions = [
        line.replace(" [BREAK] ", "\n").strip()
        for line in f
        if line.strip()
    ]

print(f"Total entries to index: {len(questions)}")

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print(f"Loading embedding model: {MODEL_NAME} ...")
embedder = SentenceTransformer(MODEL_NAME)

print("Encoding all entries (this may take a few minutes) ...")
matrix = embedder.encode(questions, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)
matrix = matrix.astype("float32")

print("Building FAISS index ...")
index = faiss.IndexFlatIP(matrix.shape[1])
index.add(matrix)

print(f"Saving index to {INDEX_PATH} ...")
faiss.write_index(index, str(INDEX_PATH))
np.save(MATRIX_PATH, matrix)

print(f"\n✅ Done! Index rebuilt with {index.ntotal} vectors.")
print("Restart the server to pick up the new index.")
