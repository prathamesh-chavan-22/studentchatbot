import re
import json
from pathlib import Path

def parse_faq_marathi(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # regex for Q: प्र.\d+) ... A: ...
    # but the format might vary. Let's try splitting.
    blocks = re.split(r'\n(?=Q:\s*प्र\.\s*\d+\))', content)
    
    faq_list = []
    for i, block in enumerate(blocks):
        if not block.strip():
            continue
        
        q_match = re.search(r'Q:\s*प्र\.\s*\d+\)\s*(.*?)(?=\n\s*A:|$)', block, re.DOTALL)
        a_match = re.search(r'A:\s*(.*?)$', block, re.DOTALL)
        
        if q_match and a_match:
            question = q_match.group(1).strip()
            answer = a_match.group(1).strip()
            # Remove any trailing extra A: or Q: from incorrect parsing
            answer = re.sub(r'Q:\s*प्र\..*$', '', answer, flags=re.DOTALL).strip()
            
            faq_list.append({
                "id": f"faq_{i+1}",
                "mr": {
                    "question": question,
                    "answer": answer
                }
            })
    
    return faq_list

if __name__ == "__main__":
    src = "/Users/apple/Dev/studentchatbot/api_based_support_bot/fyjc_faq_full.txt"
    marathi_faqs = parse_faq_marathi(src)
    
    dest = "/Users/apple/Dev/studentchatbot/semantic_support_bot/marathi_faqs_raw.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(marathi_faqs, f, ensure_ascii=False, indent=2)
    
    print(f"Extracted {len(marathi_faqs)} FAQs.")
