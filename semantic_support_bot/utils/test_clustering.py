"""
Test script to analyze embedding clustering quality for FAQ data.
This checks if embeddings are too closely clustered (which could indicate
lack of diversity or overfitting).
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics import silhouette_score, davies_bouldin_score
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
from pathlib import Path


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
                # E5 models require 'passage: ' prefix for documents
                questions.append(f"passage: {q}")
                metadata.append({
                    "id": faq_id,
                    "lang": lang,
                    "question": q,
                    "answer": answer
                })
    
    return questions, metadata, knowledge_base


def compute_embeddings(questions, model_name="intfloat/multilingual-e5-base"):
    """Compute embeddings for all questions."""
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    print(f"Computing embeddings for {len(questions)} questions...")
    embeddings = model.encode(
        questions,
        convert_to_tensor=True,
        normalize_embeddings=True
    )
    
    return embeddings.cpu().numpy(), model


def analyze_intra_faq_similarity(embeddings, metadata):
    """Analyze similarity within each FAQ group (same id)."""
    faq_groups = {}
    for i, meta in enumerate(metadata):
        faq_id = meta["id"]
        if faq_id not in faq_groups:
            faq_groups[faq_id] = []
        faq_groups[faq_id].append(i)
    
    intra_similarities = []
    for faq_id, indices in faq_groups.items():
        if len(indices) > 1:
            # Get embeddings for this FAQ group
            group_embeddings = embeddings[indices]
            # Compute pairwise cosine similarities
            similarities = []
            for i in range(len(group_embeddings)):
                for j in range(i + 1, len(group_embeddings)):
                    sim = np.dot(group_embeddings[i], group_embeddings[j])
                    similarities.append(sim)
            intra_similarities.extend(similarities)
    
    return intra_similarities, faq_groups


def analyze_inter_faq_similarity(embeddings, metadata):
    """Analyze similarity between different FAQ groups."""
    # Group by FAQ id
    faq_groups = {}
    for i, meta in enumerate(metadata):
        faq_id = meta["id"]
        if faq_id not in faq_groups:
            faq_groups[faq_id] = []
        faq_groups[faq_id].append(i)
    
    # Get representative embedding for each FAQ (mean of all its questions)
    faq_representatives = {}
    for faq_id, indices in faq_groups.items():
        faq_representatives[faq_id] = np.mean(embeddings[indices], axis=0)
    
    # Compute pairwise similarities between FAQ representatives
    faq_ids = list(faq_representatives.keys())
    inter_similarities = []
    for i in range(len(faq_ids)):
        for j in range(i + 1, len(faq_ids)):
            sim = np.dot(
                faq_representatives[faq_ids[i]], 
                faq_representatives[faq_ids[j]]
            )
            inter_similarities.append(sim)
    
    return inter_similarities


def analyze_language_separation(embeddings, metadata):
    """Analyze how well different languages are separated."""
    lang_groups = {}
    for i, meta in enumerate(metadata):
        lang = meta["lang"]
        if lang not in lang_groups:
            lang_groups[lang] = []
        lang_groups[lang].append(i)
    
    # Compute intra-language similarity
    intra_lang_sims = {}
    for lang, indices in lang_groups.items():
        if len(indices) > 1:
            group_embeddings = embeddings[indices]
            sims = []
            for i in range(len(group_embeddings)):
                for j in range(i + 1, len(group_embeddings)):
                    sims.append(np.dot(group_embeddings[i], group_embeddings[j]))
            intra_lang_sims[lang] = np.mean(sims) if sims else 0
    
    # Compute inter-language similarity (sample to avoid O(n^2))
    inter_lang_sims = []
    langs = list(lang_groups.keys())
    sample_size = 100  # Sample to keep computation manageable
    for i in range(len(langs)):
        for j in range(i + 1, len(langs)):
            indices_i = np.random.choice(lang_groups[langs[i]], min(sample_size, len(lang_groups[langs[i]])), replace=False)
            indices_j = np.random.choice(lang_groups[langs[j]], min(sample_size, len(lang_groups[langs[j]])), replace=False)
            
            sims = []
            for idx_i in indices_i:
                for idx_j in indices_j:
                    sims.append(np.dot(embeddings[idx_i], embeddings[idx_j]))
            inter_lang_sims.append(np.mean(sims))
    
    return intra_lang_sims, np.mean(inter_lang_sims) if inter_lang_sims else 0


def compute_clustering_metrics(embeddings, metadata):
    """Compute clustering quality metrics."""
    # Create labels based on FAQ id
    faq_to_label = {}
    labels = []
    for i, meta in enumerate(metadata):
        faq_id = meta["id"]
        if faq_id not in faq_to_label:
            faq_to_label[faq_id] = len(faq_to_label)
        labels.append(faq_to_label[faq_id])
    
    labels = np.array(labels)
    
    # Silhouette Score (higher is better, range: -1 to 1)
    print("\nComputing Silhouette Score...")
    silhouette = silhouette_score(embeddings, labels, sample_size=min(10000, len(embeddings)), random_state=42)
    
    # Davies-Bouldin Index (lower is better, range: 0 to inf)
    print("Computing Davies-Bouldin Index...")
    davies_bouldin = davies_bouldin_score(embeddings, labels)
    
    return silhouette, davies_bouldin


def find_problematic_clusters(embeddings, metadata, faq_groups, threshold=0.95):
    """Find FAQ groups that are too similar to each other (potential duplicates)."""
    # Get representative embedding for each FAQ
    faq_representatives = {}
    for faq_id, indices in faq_groups.items():
        faq_representatives[faq_id] = np.mean(embeddings[indices], axis=0)
    
    # Find pairs with very high similarity
    faq_ids = list(faq_representatives.keys())
    problematic_pairs = []
    
    for i in range(len(faq_ids)):
        for j in range(i + 1, len(faq_ids)):
            sim = np.dot(
                faq_representatives[faq_ids[i]], 
                faq_representatives[faq_ids[j]]
            )
            if sim > threshold:
                problematic_pairs.append((faq_ids[i], faq_ids[j], sim))
    
    return sorted(problematic_pairs, key=lambda x: x[2], reverse=True)


def visualize_distribution(intra_sims, inter_sims, output_path="clustering_analysis.png"):
    """Create visualization of similarity distributions."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histogram of similarities
    axes[0].hist(intra_sims, bins=30, alpha=0.7, label='Intra-FAQ (same topic)', color='green')
    axes[0].hist(inter_sims, bins=30, alpha=0.7, label='Inter-FAQ (different topics)', color='red')
    axes[0].axvline(np.mean(intra_sims), color='green', linestyle='dashed', linewidth=2, label=f'Intra mean: {np.mean(intra_sims):.3f}')
    axes[0].axvline(np.mean(inter_sims), color='red', linestyle='dashed', linewidth=2, label=f'Inter mean: {np.mean(inter_sims):.3f}')
    axes[0].set_xlabel('Cosine Similarity')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Distribution of Similarities')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Separation analysis
    separation = np.mean(intra_sims) - np.mean(inter_sims)
    overlap = sum(1 for s in inter_sims if s > np.mean(intra_sims) - np.std(intra_sims)) / len(inter_sims)
    
    axes[1].bar(['Separation', 'Overlap %'], [separation, overlap * 100], color=['blue', 'orange'])
    axes[1].set_ylabel('Value')
    axes[1].set_title(f'Clustering Quality\n(Separation: {separation:.3f}, Overlap: {overlap*100:.1f}%)')
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"\nVisualization saved to: {output_path}")
    plt.close()


def main():
    print("=" * 70)
    print("FAQ Embedding Clustering Analysis")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading questions from questions_answers.json...")
    questions, metadata, knowledge_base = load_questions()
    print(f"   Loaded {len(questions)} questions from {len(knowledge_base)} FAQ groups")
    print(f"   Languages: {set(m['lang'] for m in metadata)}")
    
    # Compute embeddings
    print("\n2. Computing embeddings...")
    embeddings, model = compute_embeddings(questions)
    print(f"   Embedding shape: {embeddings.shape}")
    print(f"   Embedding dimensions: {embeddings.shape[1]}")
    
    # Analyze intra-FAQ similarity
    print("\n3. Analyzing Intra-FAQ Similarity (within same topic)...")
    intra_sims, faq_groups = analyze_intra_faq_similarity(embeddings, metadata)
    print(f"   Mean intra-FAQ similarity: {np.mean(intra_sims):.4f}")
    print(f"   Std intra-FAQ similarity: {np.std(intra_sims):.4f}")
    print(f"   Min intra-FAQ similarity: {np.min(intra_sims):.4f}")
    print(f"   Max intra-FAQ similarity: {np.max(intra_sims):.4f}")
    
    # Analyze inter-FAQ similarity
    print("\n4. Analyzing Inter-FAQ Similarity (between different topics)...")
    inter_sims = analyze_inter_faq_similarity(embeddings, metadata)
    print(f"   Mean inter-FAQ similarity: {np.mean(inter_sims):.4f}")
    print(f"   Std inter-FAQ similarity: {np.std(inter_sims):.4f}")
    print(f"   Max inter-FAQ similarity: {np.max(inter_sims):.4f}")
    
    # Language separation
    print("\n5. Analyzing Language Separation...")
    intra_lang_sims, inter_lang_avg = analyze_language_separation(embeddings, metadata)
    for lang, avg_sim in intra_lang_sims.items():
        print(f"   {lang}: intra-language similarity = {avg_sim:.4f}")
    print(f"   Average inter-language similarity: {inter_lang_avg:.4f}")
    
    # Clustering metrics
    print("\n6. Computing Clustering Quality Metrics...")
    silhouette, davies_bouldin = compute_clustering_metrics(embeddings, metadata)
    print(f"   Silhouette Score: {silhouette:.4f} (range: -1 to 1, higher is better)")
    print(f"   Davies-Bouldin Index: {davies_bouldin:.4f} (range: 0 to ∞, lower is better)")
    
    # Find problematic clusters
    print("\n7. Finding Potentially Problematic Clusters (similarity > 0.95)...")
    problematic = find_problematic_clusters(embeddings, metadata, faq_groups, threshold=0.95)
    if problematic:
        print(f"   Found {len(problematic)} potentially duplicate FAQ pairs:")
        for faq1, faq2, sim in problematic[:10]:  # Show top 10
            print(f"      {faq1} ↔ {faqq2}: {sim:.4f}")
    else:
        print("   ✓ No problematic clusters found!")
    
    # Visualization
    print("\n8. Creating visualization...")
    visualize_distribution(intra_sims, inter_sims)
    
    # Summary and recommendations
    print("\n" + "=" * 70)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 70)
    
    separation = np.mean(intra_sims) - np.mean(inter_sims)
    
    if separation > 0.2:
        print("✓ GOOD: Clear separation between FAQ topics")
    elif separation > 0.1:
        print("⚠ MODERATE: Some overlap between FAQ topics")
    else:
        print("✗ POOR: FAQ topics are too closely clustered")
    
    if np.mean(intra_sims) > 0.85:
        print("✓ GOOD: Questions within same FAQ are very similar")
    else:
        print("⚠ Consider: Adding more diverse question variants within FAQs")
    
    if silhouette > 0.5:
        print("✓ GOOD: Strong clustering structure")
    elif silhouette > 0.25:
        print("⚠ MODERATE: Reasonable clustering structure")
    else:
        print("✗ POOR: Weak clustering structure - consider revising FAQs")
    
    if problematic:
        print(f"⚠ WARNING: {len(problematic)} FAQ pairs are very similar - consider merging")
    
    print("\nKey Metrics:")
    print(f"  - Intra-FAQ similarity: {np.mean(intra_sims):.4f}")
    print(f"  - Inter-FAQ similarity: {np.mean(inter_sims):.4f}")
    print(f"  - Separation: {separation:.4f}")
    print(f"  - Silhouette Score: {silhouette:.4f}")
    print(f"  - Davies-Bouldin Index: {davies_bouldin:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    main()
