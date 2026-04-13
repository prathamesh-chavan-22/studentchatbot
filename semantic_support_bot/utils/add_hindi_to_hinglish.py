#!/usr/bin/env python3
"""
Add Hindi answers to hinglish variants.
Currently hinglish uses English answers - this adds proper Hindi answers.
"""

import json
from pathlib import Path

def add_hindi_answers_to_hinglish():
    """Copy Hindi answers to hinglish variants where Hindi exists."""
    
    base_dir = Path(__file__).parent
    json_path = base_dir / "questions_answers.json"
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    updated = 0
    
    for item in data:
        hindi_answer = None
        hinglish_variant = None
        
        # Find Hindi answer and Hinglish variant
        for variant in item.get("variants", []):
            if variant.get("lang") == "hi":
                hindi_answer = variant.get("answer")
            elif variant.get("lang") == "hinglish":
                hinglish_variant = variant
        
        # Update hinglish answer with Hindi if it currently has English
        if hinglish_variant and hindi_answer:
            current_answer = hinglish_variant.get("answer", "")
            # If answer is same as English (not truly Hinglish), replace with Hindi
            en_variant = next((v for v in item["variants"] if v["lang"] == "en"), None)
            if en_variant and current_answer == en_variant.get("answer", ""):
                hinglish_variant["answer"] = hindi_answer
                updated += 1
    
    # Save
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Updated {updated} hinglish variants with Hindi answers")
    print(f"File saved: {json_path}")


if __name__ == "__main__":
    add_hindi_answers_to_hinglish()
