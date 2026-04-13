#!/usr/bin/env python3
"""
Migration script to convert questions_answers.json from old schema to new variants schema.

Old Schema:
{
  "id": "faq_1",
  "en": { "question": "...", "answer": "..." },
  "mr": { "question": "...", "answer": "..." },
  "hi": { "question": "...", "answer": "..." }
}

New Schema:
{
  "id": "faq_1",
  "variants": [
    {
      "lang": "en",
      "questions": ["...", "..."],
      "answer": "..."
    },
    {
      "lang": "mr",
      "questions": ["...", "..."],
      "answer": "..."
    },
    {
      "lang": "hi",
      "questions": ["...", "..."],
      "answer": "..."
    },
    {
      "lang": "hinglish",
      "questions": ["...", "..."],
      "answer": "..."
    }
  ]
}
"""

import json
from pathlib import Path
from datetime import datetime

def migrate_schema(input_path: str, output_path: str = None):
    """Migrate old JSON schema to new variants schema."""
    
    if output_path is None:
        # Create backup name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = input_path.replace(".json", f"_backup_{timestamp}.json")
    
    # Load old data
    with open(input_path, "r", encoding="utf-8") as f:
        old_data = json.load(f)
    
    new_data = []
    
    for item in old_data:
        faq_id = item["id"]
        variants = []
        
        # Process each language (en, mr, hi)
        for lang in ["en", "mr", "hi"]:
            if lang in item:
                variant = {
                    "lang": lang,
                    "questions": [item[lang]["question"]],  # Start with original question
                    "answer": item[lang]["answer"]
                }
                variants.append(variant)
        
        # Add empty hinglish variant (to be filled later)
        # Use English answer as base for hinglish
        hinglish_answer = item.get("en", {}).get("answer", "")
        variants.append({
            "lang": "hinglish",
            "questions": [],  # To be populated manually
            "answer": hinglish_answer  # Same as English initially
        })
        
        new_item = {
            "id": faq_id,
            "variants": variants
        }
        new_data.append(new_item)
    
    return new_data


def main():
    base_dir = Path(__file__).parent
    input_file = base_dir / "questions_answers.json"
    
    print(f"Reading from: {input_file}")
    
    # Migrate
    new_data = migrate_schema(str(input_file))
    
    # Save to new file
    output_file = base_dir / "questions_answers_new.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"Migrated {len(new_data)} FAQ entries to new schema")
    print(f"Output saved to: {output_file}")
    print(f"\nStatistics:")
    total_questions = 0
    for item in new_data:
        for variant in item["variants"]:
            total_questions += len(variant["questions"])
    print(f"  Total question variants: {total_questions}")
    print(f"  Average questions per FAQ: {total_questions / len(new_data):.1f}")
    
    # Show sample
    print(f"\nSample entry (faq_1):")
    print(json.dumps(new_data[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
