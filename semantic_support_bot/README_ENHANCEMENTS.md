# Semantic Support Bot - Multilingual Enhancement

## Overview

The semantic support bot has been enhanced to support **multiple question variants per FAQ** including **Hinglish** (Hindi written in Roman script), with answers in English, Hindi, and Marathi.

## Key Improvements

### 1. New Data Schema

**Before:**
```json
{
  "id": "faq_1",
  "en": { "question": "...", "answer": "..." },
  "mr": { "question": "...", "answer": "..." },
  "hi": { "question": "...", "answer": "..." }
}
```

**After:**
```json
{
  "id": "faq_1",
  "variants": [
    {
      "lang": "en",
      "questions": ["Question 1", "Question 2", "..."],
      "answer": "..."
    },
    {
      "lang": "mr",
      "questions": ["प्रश्न १", "प्रश्न २", "..."],
      "answer": "..."
    },
    {
      "lang": "hi",
      "questions": ["प्रश्न १", "प्रश्न २", "..."],
      "answer": "..."
    },
    {
      "lang": "hinglish",
      "questions": ["Sawal 1", "Sawal 2", "..."],
      "answer": "..."  // Hindi answer for Hinglish queries
    }
  ]
}
```

### 2. Statistics

| Metric | Before | After |
|--------|--------|-------|
| Total FAQs | 48 | 48 |
| Questions per FAQ | 3 (1 per language) | ~10 (multiple variants) |
| Total Questions | 144 | 479 |
| Languages Supported | en, mr, hi | en, mr, hi, **hinglish** |
| Test Accuracy | N/A | **100%** (67 tests) |

### 3. Language Support

- **English (en)**: 144 question variants
- **Marathi (mr)**: 144 question variants  
- **Hindi (hi)**: 48 question variants
- **Hinglish (hinglish)**: 143 question variants ✨ **NEW**

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `faq_manager.py` | CLI tool to manage questions (add/edit/delete) |
| `bulk_import_questions.py` | Bulk import script for Hinglish questions |
| `add_hindi_to_hinglish.py` | Add Hindi answers to Hinglish variants |
| `migrate_to_variants.py` | Migration script from old to new schema |
| `test_comprehensive.py` | Comprehensive test suite (67 tests) |
| `questions_answers_backup_original.json` | Backup of original data |

### Modified Files

| File | Changes |
|------|---------|
| `app/bot.py` | Updated to support new schema, improved Hinglish detection |
| `questions_answers.json` | Migrated to new variants schema |

## Usage

### FAQ Manager CLI

```bash
# List all FAQs with question counts
python faq_manager.py list

# Show details of a specific FAQ
python faq_manager.py show faq_1

# Add a question
python faq_manager.py add faq_1 hinglish "FYJC admission kaise hota hai?"

# Edit a question
python faq_manager.py edit faq_1 en 2 "What is the 11th grade admission process?"

# Delete a question
python faq_manager.py delete faq_1 en 3

# Bulk add questions from file
python faq_manager.py bulk faq_1 hinglish hinglish_questions.txt

# Show statistics
python faq_manager.py stats
```

### Running the Bot

```bash
# Start the FastAPI server
python -m app.main

# Or run tests
python -m app.bot

# Run comprehensive test suite
python test_comprehensive.py
```

### API Endpoint

```bash
POST /api/chat
{
  "message": "FYJC admission kaise hota hai?",
  "history": []
}

Response:
{
  "answer": "यह महाराष्ट्र राज्य में राज्य बोर्ड से संबद्ध...",
  "match_score": 0.9143,
  "match_id": "faq_1",
  "detected_lang": "hinglish"
}
```

## Features

### 1. Multilingual Support
- Detects and responds in **4 languages**: English, Hindi, Marathi, Hinglish
- Returns answers in the user's detected language
- Fallback hierarchy: detected_lang → en → mr → hi

### 2. Hinglish Detection
Uses keyword-based scoring system:
- Detects Hindi words in Roman script (kaise, kya, hai, etc.)
- Score ≥ 2 = Hinglish
- Handles common Hinglish patterns

### 3. Confidence Threshold
- **Score ≥ 0.70**: Returns matched answer
- **Score < 0.70**: Returns "I don't know" in user's language

### 4. Multiple Question Variants
Each FAQ can have multiple question phrasings per language:
- Improves semantic matching
- Handles diverse user phrasings
- Easier to maintain and expand

## Testing Results

```
Test Summary
┌─────────────┬────────┐
│ Total Tests │ 67     │
│ Passed      │ 67     │
│ Failed      │ 0      │
│ Accuracy    │ 100.0% │
└─────────────┴────────┘

Categories Tested:
✓ English Queries (15 tests)
✓ Hinglish Queries (18 tests)
✓ Hindi Queries - Devanagari (14 tests)
✓ Marathi Queries - Devanagari (12 tests)
✓ Edge Cases & Variations (8 tests)
```

## Example Queries

### English
- "What is FYJC?"
- "How to register online?"
- "What documents are required?"

### Hinglish
- "FYJC kya hai?"
- "Online register kaise karein?"
- "Documents kya chahiye?"

### Hindi
- "कक्षा 11वीं (FYJC) ऑनलाइन प्रवेश प्रक्रिया क्या है?"
- "ऑनलाइन पंजीकरण कैसे करें?"
- "कौन से दस्तावेज आवश्यक हैं?"

### Marathi
- "इयत्ता ११ वी (FYJC) ऑनलाईन प्रवेश प्रक्रिया म्हणजे काय?"
- "ऑनलाइन नोंदणी कशी करावी?"
- "प्रवेशासाठी कोणती कागदपत्रे आवश्यक आहेत?"

## Maintenance

### Adding New Questions

1. **Single question:**
   ```bash
   python faq_manager.py add faq_1 hinglish "New question here"
   ```

2. **Bulk import:**
   - Create a text file with one question per line
   - Run: `python faq_manager.py bulk faq_1 hinglish questions.txt`

3. **Programmatic:**
   ```python
   from faq_manager import FAQManager
   manager = FAQManager()
   manager.add_question("faq_1", "hinglish", "Your question here")
   ```

### Updating Answers

```bash
python faq_manager.py answer faq_1 hi "नया उत्तर यहाँ"
```

## Dependencies

- `sentence-transformers`: Multilingual embeddings
- `langdetect`: Language detection
- `fastapi`: Web framework
- `rich`: Console output formatting
- `loguru`: Logging

Install: `pip install -r requirements.txt`

## Future Enhancements

- [ ] Add more Hinglish question variants
- [ ] Implement conversation history tracking
- [ ] Add support for images/PDFs in answers
- [ ] Integrate with WhatsApp/Telegram
- [ ] Add analytics dashboard
- [ ] Implement feedback mechanism

## Troubleshooting

### Bot not detecting Hinglish correctly
- Check if Hinglish keywords are in the query
- Add more Hinglish question variants for better matching

### Low confidence scores
- Add more question variants similar to user queries
- Check if the question is covered in the knowledge base

### Language detection errors
- The bot uses `langdetect` which may misclassify short queries
- Fallback to English is automatic for unknown languages

---

**Last Updated:** April 1, 2026  
**Version:** 1.1.0
