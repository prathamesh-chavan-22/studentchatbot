"""
Script to identify and remove duplicate FAQs based on embedding similarity.
Generates a cleaned version of questions_answers.json
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from collections import defaultdict


def load_qa(qa_path="questions_answers.json"):
    """Load QA JSON file."""
    base_dir = Path(__file__).resolve().parent
    full_path = base_dir / qa_path
    
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_faq_representative_embedding(faq_item, model):
    """Get a representative embedding for an FAQ (average of all questions)."""
    all_question_embeddings = []
    
    for variant in faq_item.get("variants", []):
        questions = variant.get("questions", [])
        for q in questions:
            prefixed = f"passage: {q}"
            emb = model.encode(prefixed, convert_to_tensor=True, normalize_embeddings=True)
            all_question_embeddings.append(emb.cpu().numpy())
    
    if not all_question_embeddings:
        return None
    
    # Average all embeddings
    avg_embedding = np.mean(all_question_embeddings, axis=0)
    # Re-normalize
    avg_embedding /= np.linalg.norm(avg_embedding)
    return avg_embedding


def find_duplicate_groups(qa_data, model, threshold=0.98):
    """Find groups of FAQs that are duplicates (above similarity threshold)."""
    print(f"Computing embeddings for {len(qa_data)} FAQs...")
    
    # Compute representative embedding for each FAQ
    faq_embeddings = {}
    for item in qa_data:
        faq_id = item["id"]
        emb = get_faq_representative_embedding(item, model)
        if emb is not None:
            faq_embeddings[faq_id] = emb
    
    faq_ids = list(faq_embeddings.keys())
    n = len(faq_ids)
    
    # Build similarity matrix and find duplicates
    # Use Union-Find to group duplicates
    parent = {faq_id: faq_id for faq_id in faq_ids}
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    print("Finding duplicate pairs...")
    duplicate_pairs = []
    
    for i in range(n):
        for j in range(i + 1, n):
            faq_id1, faq_id2 = faq_ids[i], faq_ids[j]
            sim = np.dot(faq_embeddings[faq_id1], faq_embeddings[faq_id2])
            
            if sim > threshold:
                duplicate_pairs.append((faq_id1, faq_id2, sim))
                union(faq_id1, faq_id2)
    
    # Group by connected components
    groups = defaultdict(list)
    for faq_id in faq_ids:
        groups[find(faq_id)].append(faq_id)
    
    # Filter to only groups with more than 1 element (actual duplicates)
    duplicate_groups = {root: members for root, members in groups.items() if len(members) > 1}
    
    return duplicate_groups, duplicate_pairs


def merge_faqs(qa_data, duplicate_groups, strategy="keep_first"):
    """Merge duplicate FAQ groups into single FAQs."""
    faq_id_to_item = {item["id"]: item for item in qa_data}
    
    # Track which FAQs to keep and which to remove
    to_remove = set()
    merged_faqs = []
    
    for root, members in duplicate_groups.items():
        # Sort members to have consistent ordering
        members_sorted = sorted(members)
        
        # Keep the first one (or use other strategies)
        keeper = members_sorted[0]
        to_remove.update(members_sorted[1:])
        
        # Merge questions from all duplicates into the keeper
        keeper_item = faq_id_to_item[keeper]
        
        for member in members_sorted[1:]:
            member_item = faq_id_to_item[member]
            
            # Merge questions from each language variant
            for variant in member_item.get("variants", []):
                lang = variant.get("lang")
                questions_to_add = variant.get("questions", [])
                answer = variant.get("answer", "")
                
                # Find corresponding variant in keeper
                keeper_variant = None
                for kv in keeper_item.get("variants", []):
                    if kv.get("lang") == lang:
                        keeper_variant = kv
                        break
                
                if keeper_variant:
                    # Merge questions, avoiding exact duplicates
                    existing_questions = set(keeper_variant.get("questions", []))
                    for q in questions_to_add:
                        if q not in existing_questions:
                            keeper_variant["questions"].append(q)
                            existing_questions.add(q)
                else:
                    # Add entire variant if lang doesn't exist in keeper
                    keeper_item["variants"].append(variant)
        
        merged_faqs.append(keeper_item)
    
    # Keep non-duplicate FAQs as-is
    all_duplicate_ids = set()
    for members in duplicate_groups.values():
        all_duplicate_ids.update(members)
    
    final_faqs = merged_faqs + [item for item in qa_data if item["id"] not in all_duplicate_ids]
    
    # Sort by ID to maintain order
    final_faqs.sort(key=lambda x: x["id"])
    
    return final_faqs, to_remove


def analyze_and_clean(duplicate_pairs, duplicate_groups, qa_data, cleaned_data, removed_ids):
    """Print analysis of what was changed."""
    print("\n" + "=" * 80)
    print("DUPLICATE REMOVAL ANALYSIS")
    print("=" * 80)
    
    print(f"\nOriginal FAQ count: {len(qa_data)}")
    print(f"Cleaned FAQ count: {len(cleaned_data)}")
    print(f"FAQs removed (merged): {len(removed_ids)}")
    
    print("\n" + "-" * 80)
    print("DUPLICATE GROUPS FOUND")
    print("-" * 80)
    
    for root, members in duplicate_groups.items():
        print(f"\nGroup: {', '.join(members)}")
        for member in members:
            item = next((x for x in qa_data if x["id"] == member), None)
            if item and item.get("variants"):
                # Get English answer or first answer
                answer = "No answer"
                for variant in item["variants"]:
                    if variant.get("lang") == "en":
                        answer = variant.get("answer", "No answer")[:100]
                        break
                if answer == "No answer" and item["variants"]:
                    answer = item["variants"][0].get("answer", "No answer")[:100]
                print(f"  - {member}: {answer}...")
    
    print("\n" + "-" * 80)
    print("TOP DUPLICATE PAIRS (by similarity)")
    print("-" * 80)
    
    duplicate_pairs_sorted = sorted(duplicate_pairs, key=lambda x: x[2], reverse=True)
    for faq1, faq2, sim in duplicate_pairs_sorted[:20]:
        print(f"  {faq1} ↔ {faq2}: {sim:.4f}")


def main():
    print("=" * 80)
    print("FAQ Duplicate Detection and Removal")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading questions_answers.json...")
    qa_data = load_qa()
    print(f"   Loaded {len(qa_data)} FAQs")
    
    # Load model
    print("\n2. Loading embedding model...")
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    
    # Find duplicates with very high threshold (0.995 for exact/near-exact duplicates)
    print("\n3. Finding duplicate FAQs (threshold: 0.995)...")
    duplicate_groups, duplicate_pairs = find_duplicate_groups(qa_data, model, threshold=0.995)
    
    print(f"\n   Found {len(duplicate_groups)} duplicate groups")
    print(f"   Found {len(duplicate_pairs)} duplicate pairs")
    
    if not duplicate_groups:
        print("\n✓ No duplicates found!")
        return
    
    # Merge duplicates
    print("\n4. Merging duplicate FAQs...")
    cleaned_data, removed_ids = merge_faqs(qa_data, duplicate_groups, strategy="keep_first")
    
    # Analyze changes
    analyze_and_clean(duplicate_pairs, duplicate_groups, qa_data, cleaned_data, removed_ids)
    
    # Save cleaned data
    print("\n5. Saving cleaned data...")
    base_dir = Path(__file__).resolve().parent
    output_path = base_dir / "questions_answers_cleaned.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n   ✓ Cleaned data saved to: {output_path}")
    
    # Save detailed report
    report_path = base_dir / "duplicate_removal_report.json"
    report = {
        "original_count": len(qa_data),
        "cleaned_count": len(cleaned_data),
        "removed_count": len(removed_ids),
        "duplicate_groups": {root: members for root, members in duplicate_groups.items()},
        "duplicate_pairs": [
            {"faq1": f1, "faq2": f2, "similarity": float(s)}
            for f1, f2, s in sorted(duplicate_pairs, key=lambda x: x[2], reverse=True)
        ],
        "removed_ids": list(removed_ids)
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Detailed report saved to: {report_path}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Removed {len(removed_ids)} duplicate FAQs")
    print(f"Reduction: {len(removed_ids) / len(qa_data) * 100:.1f}%")
    print("\nTo apply the changes:")
    print(f"  1. Review: {output_path}")
    print(f"  2. If satisfied, replace: questions_answers.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
