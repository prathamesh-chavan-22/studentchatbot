#!/usr/bin/env python3
"""Script to detect duplicates in questions_answers.json"""

import json
from collections import defaultdict

def load_faqs(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_duplicates(faqs):
    """Find duplicate questions and answers"""
    
    # Track all questions and their locations
    question_map = defaultdict(list)  # question_text -> [(faq_id, lang, variant_index, question_index)]
    answer_map = defaultdict(list)    # answer_text -> [(faq_id, lang)]
    
    all_questions = []
    
    for faq in faqs:
        faq_id = faq.get('id', 'unknown')
        for variant in faq.get('variants', []):
            lang = variant.get('lang', 'unknown')
            answer = variant.get('answer', '').strip()
            
            # Track answer
            answer_map[answer].append((faq_id, lang))
            
            # Track questions
            for idx, question in enumerate(variant.get('questions', [])):
                q_text = question.strip()
                question_map[q_text].append((faq_id, lang, idx))
                all_questions.append((q_text, faq_id, lang))
    
    # Find exact duplicate questions
    duplicate_questions = {q: locs for q, locs in question_map.items() if len(locs) > 1}
    
    # Find duplicate answers (same answer for different questions)
    duplicate_answers = {a: locs for a, locs in answer_map.items() if len(locs) > 1}
    
    return duplicate_questions, duplicate_answers, question_map, answer_map

def analyze_semantic_duplicates(faqs):
    """Find potential semantic duplicates by normalizing questions"""
    
    def normalize(text):
        """Normalize text for comparison"""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    normalized_map = defaultdict(list)
    
    for faq in faqs:
        faq_id = faq.get('id', 'unknown')
        for variant in faq.get('variants', []):
            lang = variant.get('lang', 'unknown')
            for idx, question in enumerate(variant.get('questions', [])):
                normalized = normalize(question)
                if normalized:
                    normalized_map[normalized].append((question, faq_id, lang))
    
    # Find duplicates (same normalized form)
    semantic_duplicates = {
        norm: questions for norm, questions in normalized_map.items() 
        if len(questions) > 1
    }
    
    return semantic_duplicates

def main():
    filepath = 'questions_answers.json'
    print(f"Loading {filepath}...")
    faqs = load_faqs(filepath)
    
    print(f"\n📊 Total FAQs: {len(faqs)}")
    
    # Count total questions and answers
    total_questions = 0
    total_variants = 0
    for faq in faqs:
        for variant in faq.get('variants', []):
            total_variants += 1
            total_questions += len(variant.get('questions', []))
    
    print(f"📊 Total Variants: {total_variants}")
    print(f"📊 Total Questions: {total_questions}")
    
    # Find exact duplicates
    print("\n🔍 Finding exact duplicate questions...")
    dup_questions, dup_answers, q_map, a_map = find_duplicates(faqs)
    
    print(f"\n❌ Exact duplicate questions found: {len(dup_questions)}")
    if dup_questions:
        print("\n--- Duplicate Questions (exact text match) ---")
        for i, (question, locations) in enumerate(list(dup_questions.items())[:20], 1):
            print(f"\n{i}. \"{question}\"")
            for loc in locations:
                print(f"   → {loc[0]} ({loc[1]}), position {loc[2]}")
        if len(dup_questions) > 20:
            print(f"\n... and {len(dup_questions) - 20} more")
    
    # Find duplicate answers
    print(f"\n📋 FAQs with identical answers: {len(dup_answers)}")
    if dup_answers:
        print("\n--- FAQs Sharing Same Answer ---")
        for i, (answer, locations) in enumerate(list(dup_answers.items())[:10], 1):
            faq_ids = set(loc[0] for loc in locations)
            if len(faq_ids) > 1:  # Only show if different FAQs share the answer
                print(f"\n{i}. Answer shared by: {', '.join(faq_ids)}")
                print(f"   Languages: {set(loc[1] for loc in locations)}")
                preview = answer[:100] + "..." if len(answer) > 100 else answer
                print(f"   Preview: {preview}")
        if len(dup_answers) > 10:
            print(f"\n... and {len(dup_answers) - 10} more")
    
    # Find semantic duplicates
    print("\n🔍 Finding semantic duplicates (normalized comparison)...")
    semantic_dups = analyze_semantic_duplicates(faqs)
    
    print(f"\n🤔 Potential semantic duplicates: {len(semantic_dups)}")
    if semantic_dups:
        print("\n--- Semantic Duplicates (first 15) ---")
        for i, (normalized, questions) in enumerate(list(semantic_dups.items())[:15], 1):
            print(f"\n{i}. Normalized: \"{normalized}\"")
            for q_text, faq_id, lang in questions:
                print(f"   → \"{q_text}\" [{faq_id}, {lang}]")
        if len(semantic_dups) > 15:
            print(f"\n... and {len(semantic_dups) - 15} more")
    
    # Summary
    print("\n" + "="*60)
    print("📝 SUMMARY")
    print("="*60)
    print(f"Total FAQs: {len(faqs)}")
    print(f"Exact duplicate questions: {len(dup_questions)}")
    print(f"FAQ groups with same answer: {len(dup_answers)}")
    print(f"Semantic duplicate groups: {len(semantic_dups)}")
    print("="*60)

if __name__ == '__main__':
    main()
