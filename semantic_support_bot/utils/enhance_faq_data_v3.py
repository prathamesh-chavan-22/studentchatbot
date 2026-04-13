#!/usr/bin/env python3
"""
Enhance FAQ JSON data with:
1. Additional Hindi question variants (currently only 1 per entry)
2. Improve Hinglish question coverage to 3+ per entry
3. Keep Hinglish answers in simple Hindi (Devanagari) as they're more readable

Note: For Hinglish, keeping answers in simple Hindi (Devanagari) is actually better
because:
- Most Hinglish speakers can read Hindi
- Romanized Hindi can be ambiguous and hard to read for long text
- Technical terms remain in English which is natural for Hinglish speakers
"""

import json
import re
from pathlib import Path


def enhance_hindi_questions(item):
    """Add 2-3 more Hindi question variants to each FAQ item."""
    variants = item.get('variants', [])
    
    # Find English and Hindi variants
    en_variant = next((v for v in variants if v.get('lang') == 'en'), None)
    hi_variant = next((v for v in variants if v.get('lang') == 'hi'), None)
    
    if not en_variant or not hi_variant:
        return False
    
    en_questions = en_variant.get('questions', [])
    hi_questions = hi_variant.get('questions', [])
    
    # If Hindi already has 3+ questions, skip
    if len(hi_questions) >= 3:
        return False
    
    # Create Hindi variations based on English questions
    new_hindi_questions = list(hi_questions)  # Start with existing
    
    # Common English to Hindi question word mappings
    hindi_question_words = {
        'What is': 'क्या है',
        'What are': 'क्या हैं',
        'How to': 'कैसे करें',
        'How can': 'कैसे कर सकते',
        'How do': 'कैसे',
        'Who can': 'कौन कर सकता',
        'Who is': 'कौन है',
        'When': 'कब',
        'Where': 'कहाँ',
        'Why': 'क्यों',
        'How many': 'कितने',
        'How much': 'कितना',
        'Is': 'क्या',
        'Are': 'क्या',
        'Can': 'क्या कर सकते',
        'Do': 'क्या',
        'Does': 'क्या',
        'Explain': 'समझाएं',
        'Describe': 'वर्णन करें',
        'Tell': 'बताएं',
        'What happens': 'क्या होता है',
        'What if': 'क्या होगा यदि',
        'What about': 'क्या के बारे में',
    }
    
    for en_q in en_questions:
        if len(new_hindi_questions) >= 3:
            break
        
        # Try to translate the question pattern
        hi_q = en_q
        translated = False
        
        for en_pattern, hi_pattern in hindi_question_words.items():
            if en_q.startswith(en_pattern):
                # Translate the question word and keep the rest
                rest = en_q[len(en_pattern):].strip()
                hi_q = f"{hi_pattern} {rest}"
                translated = True
                break
        
        # If we couldn't translate well, use a simpler approach
        if not translated:
            # Just add the English question with Hindi question marker
            hi_q = f"{en_q} (क्या है)"
        
        # Avoid duplicates
        if hi_q not in new_hindi_questions:
            new_hindi_questions.append(hi_q)
    
    # Update Hindi variant with new questions (keep first 3)
    hi_variant['questions'] = new_hindi_questions[:3]
    return True


def enhance_hinglish_questions(item):
    """Add more Hinglish question variants to reach 3+ per entry."""
    variants = item.get('variants', [])
    
    # Find English and Hinglish variants
    en_variant = next((v for v in variants if v.get('lang') == 'en'), None)
    hinglish_variant = next((v for v in variants if v.get('lang') == 'hinglish'), None)
    
    if not en_variant or not hinglish_variant:
        return False
    
    en_questions = en_variant.get('questions', [])
    hinglish_questions = hinglish_variant.get('questions', [])
    
    # If Hinglish already has 3+ questions, skip
    if len(hinglish_questions) >= 3:
        return False
    
    # Create Hinglish versions of English questions
    new_hinglish_questions = list(hinglish_questions)
    
    # Common English to Hinglish conversions (preserving common English words)
    hinglish_question_words = {
        'What is': 'Kya hai',
        'What are': 'Kya hain',
        'How to': 'Kaise karein',
        'How can': 'Kaise kar sakte',
        'How do': 'Kaise',
        'Who can': 'Kaun kar sakta',
        'Who is': 'Kaun hai',
        'When': 'Kab',
        'Where': 'Kahan',
        'Why': 'Kyun',
        'How many': 'Kitne',
        'How much': 'Kitna',
        'Is': 'Kya',
        'Are': 'Kya',
        'Can': 'Kya kar sakte',
        'Do': 'Kya',
        'Does': 'Kya',
        'Explain': 'Samjhayein',
        'Describe': 'Vivaran karein',
        'Tell': 'Batayein',
        'What happens': 'Kya hota hai',
        'What if': 'Agar toh kya hoga',
        'What about': 'Kya ke baare mein',
    }
    
    for en_q in en_questions:
        if len(new_hinglish_questions) >= 4:
            break
        
        # Convert English question to Hinglish
        hinglish_q = en_q
        
        # Translate question words
        for en_pattern, hi_pattern in hinglish_question_words.items():
            if en_q.startswith(en_pattern):
                rest = en_q[len(en_pattern):].strip()
                hinglish_q = f"{hi_pattern} {rest}"
                break
        
        # Capitalize first letter of each word for consistency
        hinglish_q = ' '.join([
            word[0].upper() + word[1:] if word else word
            for word in hinglish_q.split()
        ])
        
        # Avoid duplicates
        if hinglish_q not in new_hinglish_questions:
            new_hinglish_questions.append(hinglish_q)
    
    # Update Hinglish variant with new questions (keep first 4)
    hinglish_variant['questions'] = new_hinglish_questions[:4]
    return True


def main():
    """Main function to enhance FAQ data."""
    base_dir = Path(__file__).parent
    json_path = base_dir.parent / "questions_answers.json"
    
    print(f"Loading JSON from: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    stats = {
        'total_entries': len(data),
        'hindi_questions_enhanced': 0,
        'hinglish_questions_enhanced': 0,
    }
    
    print(f"Processing {stats['total_entries']} FAQ entries...")
    
    for i, item in enumerate(data):
        # Enhance Hindi questions
        if enhance_hindi_questions(item):
            stats['hindi_questions_enhanced'] += 1
        
        # Enhance Hinglish questions
        if enhance_hinglish_questions(item):
            stats['hinglish_questions_enhanced'] += 1
        
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{stats['total_entries']} entries...")
    
    # Save enhanced data
    output_path = base_dir.parent / "questions_answers_enhanced.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("ENHANCEMENT COMPLETE")
    print("=" * 60)
    print(f"Total entries processed: {stats['total_entries']}")
    print(f"Hindi questions enhanced: {stats['hindi_questions_enhanced']} entries")
    print(f"Hinglish questions enhanced: {stats['hinglish_questions_enhanced']} entries")
    print(f"\nOutput saved to: {output_path}")
    print("=" * 60)
    
    print("\nTo replace the original file, run:")
    print(f"  mv {output_path} {json_path}")


if __name__ == "__main__":
    main()
