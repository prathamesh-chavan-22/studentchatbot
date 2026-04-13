"""
Compare clustering quality before and after duplicate removal.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics import silhouette_score
from pathlib import Path


def load_and_compute_stats(qa_path, model):
    """Load FAQs and compute clustering statistics."""
    with open(qa_path, "r", encoding="utf-8") as f:
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
    
    # Compute embeddings
    embeddings = model.encode(questions, convert_to_tensor=True, normalize_embeddings=True)
    embeddings = embeddings.cpu().numpy()
    
    # Compute intra-FAQ similarity
    faq_groups = {}
    for i, meta in enumerate(metadata):
        faq_id = meta["id"]
        if faq_id not in faq_groups:
            faq_groups[faq_id] = []
        faq_groups[faq_id].append(i)
    
    intra_sims = []
    for faq_id, indices in faq_groups.items():
        if len(indices) > 1:
            group_embs = embeddings[indices]
            for i in range(len(group_embs)):
                for j in range(i + 1, len(group_embs)):
                    intra_sims.append(np.dot(group_embs[i], group_embs[j]))
    
    # Compute inter-FAQ similarity (using representatives)
    faq_representatives = {}
    for faq_id, indices in faq_groups.items():
        faq_representatives[faq_id] = np.mean(embeddings[indices], axis=0)
    
    inter_sims = []
    faq_ids = list(faq_representatives.keys())
    for i in range(len(faq_ids)):
        for j in range(i + 1, len(faq_ids)):
            inter_sims.append(np.dot(faq_representatives[faq_ids[i]], faq_representatives[faq_ids[j]]))
    
    # Compute silhouette score
    faq_to_label = {faq_id: i for i, faq_id in enumerate(faq_groups.keys())}
    labels = np.array([faq_to_label[meta["id"]] for meta in metadata])
    
    silhouette = silhouette_score(embeddings, labels, sample_size=min(10000, len(embeddings)), random_state=42)
    
    return {
        "num_faqs": len(faq_groups),
        "num_questions": len(questions),
        "intra_mean": np.mean(intra_sims),
        "intra_std": np.std(intra_sims),
        "inter_mean": np.mean(inter_sims),
        "inter_std": np.std(inter_sims),
        "separation": np.mean(intra_sims) - np.mean(inter_sims),
        "silhouette": silhouette
    }


def main():
    print("=" * 80)
    print("CLUSTERING QUALITY COMPARISON: Before vs After Duplicate Removal")
    print("=" * 80)
    
    # Load model
    print("\nLoading model...")
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    
    # Analyze original
    print("\nAnalyzing ORIGINAL data...")
    original_stats = load_and_compute_stats("questions_answers.json", model)
    
    # Analyze cleaned
    print("Analyzing CLEANED data...")
    cleaned_stats = load_and_compute_stats("questions_answers_cleaned.json", model)
    
    # Compare
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    
    print(f"\n{'Metric':<25} {'Original':<15} {'Cleaned':<15} {'Change':<15}")
    print("-" * 80)
    
    metrics = [
        ("Num FAQs", "num_faqs", False),
        ("Num Questions", "num_questions", False),
        ("Intra-FAQ Similarity", "intra_mean", True),
        ("Inter-FAQ Similarity", "inter_mean", False),
        ("Separation", "separation", True),
        ("Silhouette Score", "silhouette", True)
    ]
    
    for name, key, higher_better in metrics:
        orig_val = original_stats[key]
        clean_val = cleaned_stats[key]
        if higher_better:
            change = "✓" if clean_val > orig_val else "✗"
            direction = "↑" if clean_val > orig_val else "↓"
        else:
            change = "✓" if clean_val < orig_val else "✗"
            direction = "↓" if clean_val < orig_val else "↑"
        
        if key in ["num_faqs", "num_questions"]:
            print(f"{name:<25} {orig_val:<15} {clean_val:<15} {direction} {abs(clean_val - orig_val):.0f}")
        else:
            print(f"{name:<25} {orig_val:<15.4f} {clean_val:<15.4f} {direction} {abs(clean_val - orig_val):.4f} {change}")
    
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    
    separation_improvement = cleaned_stats["separation"] - original_stats["separation"]
    silhouette_improvement = cleaned_stats["silhouette"] - original_stats["silhouette"]
    
    if separation_improvement > 0.01:
        print(f"✓ Separation improved by {separation_improvement:.4f}")
    elif separation_improvement > 0:
        print(f"✓ Slight separation improvement by {separation_improvement:.4f}")
    else:
        print(f"✗ Separation decreased by {abs(separation_improvement):.4f}")
    
    if silhouette_improvement > 0.01:
        print(f"✓ Silhouette score improved by {silhouette_improvement:.4f}")
    elif silhouette_improvement > 0:
        print(f"✓ Slight silhouette improvement by {silhouette_improvement:.4f}")
    else:
        print(f"✗ Silhouette score decreased by {abs(silhouette_improvement):.4f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
