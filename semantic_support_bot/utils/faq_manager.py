#!/usr/bin/env python3
"""
CLI tool to manage questions_answers.json
- Add/edit/delete questions per FAQ ID
- Add question variants in any language (en, mr, hi, hinglish)
- Bulk import questions from CSV/text files
"""

import json
import sys
from pathlib import Path
from typing import Optional, List

class FAQManager:
    def __init__(self, json_path: str = "questions_answers.json"):
        self.base_dir = Path(__file__).parent
        self.json_path = self.base_dir / json_path
        self.data = self._load()
    
    def _load(self) -> List[dict]:
        """Load JSON data."""
        if not self.json_path.exists():
            print(f"Error: File not found at {self.json_path}")
            sys.exit(1)
        
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save(self):
        """Save JSON data."""
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved changes to {self.json_path}")
    
    def _find_faq(self, faq_id: str) -> Optional[dict]:
        """Find FAQ entry by ID."""
        for item in self.data:
            if item["id"] == faq_id:
                return item
        return None
    
    def _find_variant(self, faq: dict, lang: str) -> Optional[dict]:
        """Find language variant within FAQ."""
        for variant in faq["variants"]:
            if variant["lang"] == lang:
                return variant
        return None
    
    def list_faqs(self):
        """List all FAQ IDs with question counts."""
        print(f"\n{'ID':<12} {'en':<5} {'mr':<5} {'hi':<5} {'hinglish':<5}")
        print("-" * 40)
        for item in self.data:
            counts = {lang: 0 for lang in ["en", "mr", "hi", "hinglish"]}
            for variant in item["variants"]:
                counts[variant["lang"]] = len(variant["questions"])
            print(f"{item['id']:<12} {counts['en']:<5} {counts['mr']:<5} {counts['hi']:<5} {counts['hinglish']:<5}")
        print(f"\nTotal FAQs: {len(self.data)}")
    
    def show_faq(self, faq_id: str):
        """Show full details of a specific FAQ."""
        faq = self._find_faq(faq_id)
        if not faq:
            print(f"Error: FAQ '{faq_id}' not found")
            return
        
        print(f"\n{'='*60}")
        print(f"FAQ: {faq_id}")
        print(f"{'='*60}")
        
        for variant in faq["variants"]:
            lang = variant["lang"]
            print(f"\n[{lang.upper()}]")
            print(f"Answer: {variant['answer'][:100]}..." if len(variant['answer']) > 100 else f"Answer: {variant['answer']}")
            print(f"Questions ({len(variant['questions'])}):")
            for i, q in enumerate(variant["questions"], 1):
                print(f"  {i}. {q}")
    
    def add_question(self, faq_id: str, lang: str, question: str):
        """Add a new question variant to an FAQ."""
        faq = self._find_faq(faq_id)
        if not faq:
            print(f"Error: FAQ '{faq_id}' not found")
            return False
        
        variant = self._find_variant(faq, lang)
        if not variant:
            # Create new language variant
            # Copy answer from English if available
            answer = ""
            en_variant = self._find_variant(faq, "en")
            if en_variant:
                answer = en_variant["answer"]
            
            variant = {"lang": lang, "questions": [], "answer": answer}
            faq["variants"].append(variant)
            print(f"✓ Created new '{lang}' variant for {faq_id}")
        
        if question not in variant["questions"]:
            variant["questions"].append(question)
            self._save()
            print(f"✓ Added question to {faq_id} ({lang})")
            return True
        else:
            print(f"⚠ Question already exists")
            return False
    
    def edit_question(self, faq_id: str, lang: str, question_idx: int, new_question: str):
        """Edit an existing question."""
        faq = self._find_faq(faq_id)
        if not faq:
            print(f"Error: FAQ '{faq_id}' not found")
            return False
        
        variant = self._find_variant(faq, lang)
        if not variant:
            print(f"Error: Language '{lang}' not found for {faq_id}")
            return False
        
        if question_idx < 1 or question_idx > len(variant["questions"]):
            print(f"Error: Question index out of range (1-{len(variant['questions'])})")
            return False
        
        old_q = variant["questions"][question_idx - 1]
        variant["questions"][question_idx - 1] = new_question
        self._save()
        print(f"✓ Updated question {question_idx} in {faq_id} ({lang})")
        print(f"  From: {old_q}")
        print(f"  To:   {new_question}")
        return True
    
    def delete_question(self, faq_id: str, lang: str, question_idx: int):
        """Delete a question by index."""
        faq = self._find_faq(faq_id)
        if not faq:
            print(f"Error: FAQ '{faq_id}' not found")
            return False
        
        variant = self._find_variant(faq, lang)
        if not variant:
            print(f"Error: Language '{lang}' not found for {faq_id}")
            return False
        
        if question_idx < 1 or question_idx > len(variant["questions"]):
            print(f"Error: Question index out of range (1-{len(variant['questions'])})")
            return False
        
        deleted = variant["questions"].pop(question_idx - 1)
        self._save()
        print(f"✓ Deleted question {question_idx} from {faq_id} ({lang})")
        print(f"  Deleted: {deleted}")
        return True
    
    def update_answer(self, faq_id: str, lang: str, new_answer: str):
        """Update the answer for a language variant."""
        faq = self._find_faq(faq_id)
        if not faq:
            print(f"Error: FAQ '{faq_id}' not found")
            return False
        
        variant = self._find_variant(faq, lang)
        if not variant:
            # Create new variant
            variant = {"lang": lang, "questions": [], "answer": new_answer}
            faq["variants"].append(variant)
            print(f"✓ Created new '{lang}' variant for {faq_id}")
        else:
            variant["answer"] = new_answer
        
        self._save()
        print(f"✓ Updated answer for {faq_id} ({lang})")
        return True
    
    def add_faq(self, faq_id: str, answers: dict):
        """
        Add a new FAQ entry.
        answers: dict with lang as key, {"questions": [...], "answer": "..."} as value
        """
        if self._find_faq(faq_id):
            print(f"Error: FAQ '{faq_id}' already exists")
            return False
        
        variants = []
        for lang, data in answers.items():
            variants.append({
                "lang": lang,
                "questions": data.get("questions", []),
                "answer": data.get("answer", "")
            })
        
        self.data.append({"id": faq_id, "variants": variants})
        self._save()
        print(f"✓ Added new FAQ: {faq_id}")
        return True
    
    def bulk_add_questions(self, faq_id: str, lang: str, questions: List[str]):
        """Add multiple questions at once."""
        faq = self._find_faq(faq_id)
        if not faq:
            print(f"Error: FAQ '{faq_id}' not found")
            return 0
        
        variant = self._find_variant(faq, lang)
        if not variant:
            # Create new variant
            answer = ""
            en_variant = self._find_variant(faq, "en")
            if en_variant:
                answer = en_variant["answer"]
            variant = {"lang": lang, "questions": [], "answer": answer}
            faq["variants"].append(variant)
        
        added = 0
        for q in questions:
            if q.strip() and q not in variant["questions"]:
                variant["questions"].append(q.strip())
                added += 1
        
        if added > 0:
            self._save()
        print(f"✓ Added {added} new questions to {faq_id} ({lang})")
        return added
    
    def get_stats(self):
        """Print statistics about the knowledge base."""
        total_questions = 0
        lang_counts = {"en": 0, "mr": 0, "hi": 0, "hinglish": 0}
        
        for item in self.data:
            for variant in item["variants"]:
                count = len(variant["questions"])
                total_questions += count
                if variant["lang"] in lang_counts:
                    lang_counts[variant["lang"]] += count
        
        print(f"\n{'='*40}")
        print(f"Knowledge Base Statistics")
        print(f"{'='*40}")
        print(f"Total FAQ IDs: {len(self.data)}")
        print(f"Total Questions: {total_questions}")
        print(f"\nQuestions by Language:")
        for lang, count in lang_counts.items():
            print(f"  {lang:<10}: {count}")
        print(f"\nAverage questions per FAQ: {total_questions / len(self.data):.1f}")


def print_help():
    """Print help message."""
    help_text = """
FAQ Manager - Manage questions_answers.json

Usage:
    python faq_manager.py <command> [arguments]

Commands:
    list                              - List all FAQs with question counts
    show <faq_id>                     - Show details of a specific FAQ
    stats                             - Show knowledge base statistics
    
    add <faq_id> <lang> <question>    - Add a question to an FAQ
    edit <faq_id> <lang> <idx> <q>    - Edit question at index (1-based)
    delete <faq_id> <lang> <idx>      - Delete question at index
    answer <faq_id> <lang> <answer>   - Update answer for a language
    
    bulk <faq_id> <lang> <file>       - Add questions from file (one per line)

Examples:
    python faq_manager.py list
    python faq_manager.py show faq_1
    python faq_manager.py add faq_1 hinglish "FYJC admission kaise hota hai?"
    python faq_manager.py edit faq_1 en 2 "What is the 11th grade admission process?"
    python faq_manager.py delete faq_1 en 3
    python faq_manager.py bulk faq_1 hinglish hinglish_questions.txt
    python faq_manager.py stats

Languages: en, mr, hi, hinglish
"""
    print(help_text)


def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    manager = FAQManager()
    command = sys.argv[1].lower()
    
    if command == "list":
        manager.list_faqs()
    
    elif command == "show":
        if len(sys.argv) < 3:
            print("Error: Please provide FAQ ID")
            return
        manager.show_faq(sys.argv[2])
    
    elif command == "stats":
        manager.get_stats()
    
    elif command == "add":
        if len(sys.argv) < 5:
            print("Error: Usage: add <faq_id> <lang> <question>")
            return
        faq_id = sys.argv[2]
        lang = sys.argv[3]
        question = " ".join(sys.argv[4:])
        manager.add_question(faq_id, lang, question)
    
    elif command == "edit":
        if len(sys.argv) < 6:
            print("Error: Usage: edit <faq_id> <lang> <index> <new_question>")
            return
        faq_id = sys.argv[2]
        lang = sys.argv[3]
        idx = int(sys.argv[4])
        question = " ".join(sys.argv[5:])
        manager.edit_question(faq_id, lang, idx, question)
    
    elif command == "delete":
        if len(sys.argv) < 5:
            print("Error: Usage: delete <faq_id> <lang> <index>")
            return
        faq_id = sys.argv[2]
        lang = sys.argv[3]
        idx = int(sys.argv[4])
        manager.delete_question(faq_id, lang, idx)
    
    elif command == "answer":
        if len(sys.argv) < 5:
            print("Error: Usage: answer <faq_id> <lang> <answer>")
            return
        faq_id = sys.argv[2]
        lang = sys.argv[3]
        answer = " ".join(sys.argv[4:])
        manager.update_answer(faq_id, lang, answer)
    
    elif command == "bulk":
        if len(sys.argv) < 5:
            print("Error: Usage: bulk <faq_id> <lang> <file>")
            return
        faq_id = sys.argv[2]
        lang = sys.argv[3]
        file_path = Path(sys.argv[4])
        
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]
        
        manager.bulk_add_questions(faq_id, lang, questions)
    
    elif command in ["help", "-h", "--help"]:
        print_help()
    
    else:
        print(f"Error: Unknown command '{command}'")
        print_help()


if __name__ == "__main__":
    main()
