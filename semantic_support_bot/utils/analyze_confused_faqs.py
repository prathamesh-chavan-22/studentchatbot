"""
Detailed analysis: Find which FAQ topics are most confused with each other.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict


def load_questions(qa_path="questions_answers.json"):
    """Load all questions from the QA JSON file."""
    base_dir = Path(__file__).resolve().parent
    full_path = base_dir / qa_path
    
    with open(full_path, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)
    
    questions = []
    metadata = []
    
    for item in knowledge_base:
        faq_id = item["id"]
        for variant in item.get("variants", []):
            lang = variant.get("lang", "en")
            answer = variant.get("answer", "")
            for q in variant.get("questions", []):
                questions.append(f"passage: {q}")
                metadata.append({
                    "id": faq_id,
                    "lang": lang,
                    "question": q,
                    "answer": answer
                })
    
    return questions, metadata, knowledge_base


def find_most_confused_faqs(qa_path="questions_answers.json", model_name="intfloat/multilingual-e5-base", top_k=20):
    """Find FAQ pairs that are most similar to each other."""
    print("Loading data...")
    questions, metadata, knowledge_base = load_questions(qa_path)
    
    print(f"Computing embeddings...")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(questions, convert_to_tensor=True, normalize_embeddings=True)
    embeddings = embeddings.cpu().numpy()
    
    # Get representative embedding for each FAQ (mean across all questions)
    faq_embeddings = {}
    faq_questions_count = {}
    for i, meta in enumerate(metadata):
        faq_id = meta["id"]
        if faq_id not in faq_embeddings:
            faq_embeddings[faq_id] = 0
            faq_questions_count[faq_id] = 0
        faq_embeddings[faq_id] += embeddings[i]
        faq_questions_count[faq_id] += 1
    
    # Normalize by count
    for faq_id in faq_embeddings:
        faq_embeddings[faq_id] /= faq_questions_count[faq_id]
        # Re-normalize after averaging
        faq_embeddings[faq_id] /= np.linalg.norm(faq_embeddings[faq_id])
    
    # Compute similarity matrix for FAQ representatives
    faq_ids = list(faq_embeddings.keys())
    n_faqs = len(faq_ids)
    
    print(f"Computing similarity matrix for {n_faqs} FAQs...")
    similarities = []
    for i in range(n_faqs):
        for j in range(i + 1, n_faqs):
            sim = np.dot(faq_embeddings[faq_ids[i]], faq_embeddings[faq_ids[j]])
            similarities.append((faq_ids[i], faq_ids[j], sim))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[2], reverse=True)
    
    # Get FAQ answers for display
    faq_answers = {}
    for item in knowledge_base:
        # Get English answer if available, otherwise first answer
        answer = None
        for variant in item.get("variants", []):
            if variant.get("lang") == "en":
                answer = variant.get("answer", "")
                break
        if not answer:
            for variant in item.get("variants", []):
                answer = variant.get("answer", "")
                break
        faq_answers[item["id"]] = answer[:100] + "..." if len(answer) > 100 else answer
    
    # Display top confused pairs
    print("\n" + "=" * 80)
    print("TOP 20 MOST CONFUSED FAQ PAIRS (Highest Inter-FAQ Similarity)")
    print("=" * 80)
    
    for i, (faq1, faq2, sim) in enumerate(similarities[:top_k], 1):
        print(f"\n{i}. Similarity: {sim:.4f}")
        print(f"   {faq1}: {faq_answers[faq1]}")
        print(f"   {faq2}: {faq_answers[faq2]}")
    
    # Analyze by language
    print("\n" + "=" * 80)
    print("ANALYSIS BY LANGUAGE")
    print("=" * 80)
    
    # Group questions by FAQ and language
    faq_lang_embeddings = defaultdict(dict)
    for i, meta in enumerate(metadata):
        faq_id = meta["id"]
        lang = meta["lang"]
        if lang not in faq_lang_embeddings[faq_id]:
            faq_lang_embeddings[faq_id][lang] = []
        faq_lang_embeddings[faq_id][lang].append(embeddings[i])
    
    # Average within each FAQ-lang group
    for faq_id in faq_lang_embeddings:
        for lang in faq_lang_embeddings[faq_id]:
            embs = faq_lang_embeddings[faq_id][lang]
            if len(embs) > 1:
                avg_emb = np.mean(embs, axis=0)
                avg_emb /= np.linalg.norm(avg_emb)
                faq_lang_embeddings[faq_id][lang] = avg_emb
            else:
                faq_lang_embeddings[faq_id][lang] = embs[0]
    
    # Compute intra-FAQ cross-language similarity
    print("\nIntra-FAQ Cross-Language Similarity (same topic, different languages):")
    cross_lang_sims = defaultdict(list)
    for faq_id in faq_lang_embeddings:
        langs = list(faq_lang_embeddings[faq_id].keys())
        for i in range(len(langs)):
            for j in range(i + 1, len(langs)):
                lang1, lang2 = langs[i], langs[j]
                sim = np.dot(
                    faq_lang_embeddings[faq_id][lang1],
                    faq_lang_embeddings[faq_id][lang2]
                )
                cross_lang_sims[(lang1, lang2)].append(sim)
    
    for (lang1, lang2), sims in sorted(cross_lang_sims.items()):
        print(f"  {lang1} ↔ {lang2}: mean={np.mean(sims):.4f}, std={np.std(sims):.4f} (n={len(sims)})")
    
    # Find FAQs with lowest intra-FAQ similarity (most diverse questions)
    print("\n" + "=" * 80)
    print("FAQs WITH LOWEST INTRA-FAQ SIMILARITY (Most Diverse Question Wording)")
    print("=" * 80)
    
    # Reload to get intra-FAQ analysis
    faq_groups = defaultdict(list)
    for i, meta in enumerate(metadata):
        faq_groups[meta["id"]].append(i)
    
    intra_faq_diversity = []
    for faq_id, indices in faq_groups.items():
        if len(indices) > 1:
            group_embs = embeddings[indices]
            # Compute average pairwise similarity
            sims = []
            for i in range(len(group_embs)):
                for j in range(i + 1, len(group_embs)):
                    sims.append(np.dot(group_embs[i], group_embs[j]))
            avg_sim = np.mean(sims)
            intra_faq_diversity.append((faq_id, avg_sim, len(indices)))
    
    # Sort by diversity (lower similarity = more diverse)
    intra_faq_diversity.sort(key=lambda x: x[1])
    
    for faq_id, avg_sim, n_questions in intra_faq_diversity[:10]:
        print(f"\n{faq_id} (n={n_questions} questions, avg_sim={avg_sim:.4f})")
        print(f"  Answer: {faq_answers[faq_id]}")
    
    # Save confused pairs to file
    output_file = Path(__file__).resolve().parent / "confused_faqs_analysis.json"
    confused_data = {
        "top_confused_pairs": [
            {"faq1": f1, "faq2": f2, "similarity": float(s)}
            for f1, f2, s in similarities[:50]
        ],
        "cross_language_sims": {
            f"{l1}_{l2}": {"mean": float(np.mean(sims)), "std": float(np.std(sims))}
            for (l1, l2), sims in cross_lang_sims.items()
        },
        "most_diverse_faqs": [
            {"faq_id": f_id, "avg_intra_similarity": float(avg), "num_questions": n}
            for f_id, avg, n in intra_faq_diversity[:20]
        ]
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(confused_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nDetailed analysis saved to: {output_file}")
    
    return similarities


if __name__ == "__main__":
    find_most_confused_faqs()
