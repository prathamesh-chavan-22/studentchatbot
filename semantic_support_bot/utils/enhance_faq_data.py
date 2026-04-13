#!/usr/bin/env python3
"""
Enhance FAQ JSON data with:
1. Additional Hindi question variants (currently only 1 per entry)
2. Convert Hinglish answers from Devanagari to Romanized script
3. Improve Hinglish question coverage to 3+ per entry
"""

import json
import re
from pathlib import Path

# Hindi to Hinglish transliteration mapping
HINDI_TO_HINGLISH_MAP = {
    'क्या': 'kya', 'है': 'hai', 'यह': 'yeh', 'यह': 'yah', 'और': 'aur', 'में': 'mein', 'मैं': 'main',
    'का': 'ka', 'की': 'ki', 'के': 'ke', 'को': 'ko', 'से': 'se', 'पर': 'par', 'में': 'mein',
    'हैं': 'hain', 'होगा': 'hoga', 'होगी': 'hogi', 'करना': 'karna', 'कर सकते': 'kar sakte',
    'कर सकता': 'kar sakta', 'कर सकती': 'kar sakti', 'जाता': 'jata', 'जाती': 'jati',
    'रखा': 'rakha', 'दिया': 'diya', 'लिया': 'liya', 'पिया': 'piya', 'लिया': 'liya',
    'एक': 'ek', 'दो': 'do', 'तीन': 'teen', 'चार': 'chaar', 'पांच': 'paanch',
    'सभी': 'sabhi', 'सब': 'sab', 'कभी': 'kabhi', 'कहाँ': 'kahan', 'कहाँ': 'kahan',
    'यहाँ': 'yahan', 'वहाँ': 'wahan', 'अब': 'ab', 'तब': 'tab', 'जब': 'jab', 'तक': 'tak',
    'बहुत': 'bahut', 'कुछ': 'kuch', 'कौन': 'kaun', 'क्या': 'kya', 'कैसे': 'kaise',
    'कितना': 'kitna', 'कितनी': 'kitni', 'कितने': 'kitne', 'क्यों': 'kyun', 'कब': 'kab',
    'हाँ': 'haan', 'नहीं': 'nahin', 'ना': 'na', 'अगर': 'agar', 'यदि': 'yadi', 'तो': 'to',
    'भी': 'bhi', 'ही': 'hi', 'तक': 'tak', 'से': 'se', 'का': 'ka', 'की': 'ki', 'के': 'ke',
    'आप': 'aap', 'आपका': 'aapka', 'आपकी': 'aapki', 'आपके': 'aapke', 'हम': 'hum',
    'हमारा': 'hamara', 'हमारी': 'hamari', 'हमारे': 'hamare', 'तुम': 'tum', 'तेरा': 'tera',
    'तेरी': 'teri', 'मेरा': 'mera', 'मेरी': 'meri', 'मेरे': 'mere',
    'ऑनलाइन': 'online', 'ऑफलाइन': 'offline', 'फॉर्म': 'form', 'एप्लीकेशन': 'application',
    'प्रवेश': 'praves', 'एडमिशन': 'admission', 'कॉलेज': 'college', 'स्कूल': 'school',
    'फीस': 'fees', 'शुल्क': 'shulk', 'पेमेंट': 'payment', 'रजिस्ट्रेशन': 'registration',
    'लॉगिन': 'login', 'पासवर्ड': 'password', 'आईडी': 'ID', 'अकाउंट': 'account',
    'वेबसाइट': 'website', 'पोर्टल': 'portal', 'लिंक': 'link', 'बटन': 'button',
    'क्लिक': 'click', 'सिलेक्ट': 'select', 'सबमिट': 'submit', 'अपलोड': 'upload',
    'डाउनलोड': 'download', 'प्रिंट': 'print', 'चेक': 'check', 'वेरिफाई': 'verify',
    'अपडेट': 'update', 'एडिट': 'edit', 'डिलीट': 'delete', 'कैंसल': 'cancel',
    'कन्फर्म': 'confirm', 'सेव': 'save', 'नोटिफिकेशन': 'notification', 'मैसेज': 'message',
    'एसएमएस': 'SMS', 'ईमेल': 'email', 'फोन': 'phone', 'नंबर': 'number',
    'राउंड': 'round', 'सीट': 'seat', 'अलॉटमेंट': 'allotment', 'लिस्ट': 'list',
    'कैटेगरी': 'category', 'रिजर्वेशन': 'reservation', 'कोटा': 'quota', 'सर्टिफिकेट': 'certificate',
    'दस्तावेज': 'dastavez', 'मार्कशीट': 'marksheet', 'कार्ड': 'card', 'बुकलेट': 'booklet',
    'गाइडलाइन': 'guideline', 'प्रोसेस': 'process', 'स्टेप': 'step', 'तरीका': 'tarika',
    'समस्या': 'samasya', 'शिकायत': 'shikayat', 'ग्रीवेंस': 'grievance', 'हेल्प': 'help',
    'सहायता': 'sahayata', 'मदद': 'madad', 'संपर्क': 'sampark', 'कॉल': 'call',
    'समय': 'samay', 'तारीख': 'tareekh', 'दिन': 'din', 'साल': 'saal', 'महीने': 'mahine',
    'घंटे': 'ghante', 'मिनट': 'minute', 'बजे': 'baje', 'पहले': 'pehle', 'बाद': 'baad',
    'पहले': 'pehle', 'नया': 'naya', 'नई': 'nayi', 'नए': 'naye', 'पुराना': 'purana',
    'छात्र': 'chhatra', 'विद्यार्थी': 'vidyarthi', 'स्टूडेंट': 'student', 'टीचर': 'teacher',
    'प्रोफेसर': 'professor', 'क्लास': 'class', 'कोर्स': 'course', 'सब्जेक्ट': 'subject',
    'एग्जाम': 'exam', 'टेस्ट': 'test', 'रिजल्ट': 'result', 'ग्रेड': 'grade',
    'अंक': 'ank', 'नंबर': 'number', 'परसेंटाइल': 'percentile', 'रैंक': 'rank',
    'महाराष्ट्र': 'Maharashtra', 'राज्य': 'rajya', 'बोर्ड': 'board', 'विभाग': 'vibhag',
    'विज्ञान': 'vigyan', 'कॉमर्स': 'commerce', 'आर्ट्स': 'arts', 'स्ट्रीम': 'stream',
    'शाखा': 'shakha', 'विषय': 'vishay', 'अंग्रेजी': 'angrezi', 'हिंदी': 'hindi',
    'मराठी': 'marathi', 'गणित': 'ganit', 'विज्ञान': 'science', 'सामान्य': 'samanya',
    'जनरल': 'general', 'ओबीसी': 'OBC', 'एससी': 'SC', 'एसटी': 'ST', 'ईडब्ल्यूएस': 'EWS',
    'आर्थिक': 'aarthik', 'कमजोर': 'kamzor', 'वर्ग': 'varg', 'श्रेणी': 'shreni',
    'अभ्यर्थी': 'abhyarthi', 'उम्मीदवार': 'ummidwar', 'आवेदक': 'avedak', 'परीक्षा': 'pariksha',
    'परिणाम': 'parinaam', 'नतीजा': 'nateeja', 'घोषणा': 'ghoshna', 'प्रकाशित': 'prakashit',
    'जारी': 'jaari', 'अपडेट': 'update', 'सूचना': 'soochana', 'अधिसूचना': 'adhisochna',
    'दिशा': 'disha', 'निर्देश': 'nirdesh', 'गाइडलाइन': 'guideline', 'नियम': 'niyam',
    'शर्त': 'shart', 'पात्रता': 'patrata', 'योग्यता': 'yogyata', 'मानदंड': 'mandand',
    'अनिवार्य': 'anivarya', 'जरूरी': 'zaroori', 'आवश्यक': 'aavashyak', 'लागू': 'laagu',
    'लागू नहीं': 'laagu nahin', 'मान्य': 'manya', 'अमान्य': 'amanya', 'स्वीकार': 'sweekar',
    'अस्वीकार': 'asweekar', 'मंजूरी': 'manjoori', 'अनुमति': 'anumati', 'अनुमोदन': 'anumodan',
    'अस्वीकृति': 'asweekriti', 'खारिज': 'khariz', 'रद्द': 'radd', 'निलंबित': 'nilambit',
    'सक्रिय': 'sakriya', 'निष्क्रिय': 'nishkriya', 'चालू': 'chaalu', 'बंद': 'band',
    'शुरू': 'shuru', 'समाप्त': 'samaapt', 'पूरा': 'poora', 'अधूरा': 'adhoora',
    'सफल': 'safal', 'विफल': 'vifal', 'सही': 'sahi', 'गलत': 'galat',
    'ठीक': 'theek', 'गड़बड़': 'gadbad', 'त्रुटि': 'truti', 'गलती': 'galti',
    'समस्या': 'samasya', 'दिक्कत': 'dikkat', 'परेशानी': 'pareshani', 'तकलीफ': 'takleef',
    'शिकायत': 'shikayat', 'निवारण': 'nivaaran', 'समाधान': 'samaadhaan', 'हल': 'hal',
}

# Common Hindi to Hinglish character mappings
CHAR_MAP = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'an', 'अः': 'ah',
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'च': 'ch', 'छ': 'chh',
    'ज': 'j', 'झ': 'jh', 'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh',
    'ण': 'n', 'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm', 'य': 'y',
    'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's',
    'ह': 'h', 'ळ': 'l', 'क्ष': 'ksh', 'ज्ञ': 'gy', 'त्र': 'tr',
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'े': 'e',
    'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', 'ः': 'h',
    '्': '', '।': '.', '॥': '.', '०': '0', '१': '1', '२': '2', '३': '3',
    '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    '(': '(', ')': ')', ',': ',', '.': '.', '?': '?', '!': '!',
}


def transliterate_hindi_to_hinglish(hindi_text):
    """Convert Hindi text in Devanagari to Hinglish (Romanized Hindi)."""
    if not hindi_text:
        return hindi_text
    
    # First, try word-by-word translation using the map
    words = hindi_text.split()
    hinglish_words = []
    
    for word in words:
        # Remove punctuation for lookup
        clean_word = re.sub(r'[^\w]', '', word)
        punctuation = re.sub(r'[\w]', '', word)
        
        # Check if word is in our map
        if clean_word in HINDI_TO_HINGLISH_MAP:
            hinglish_word = HINDI_TO_HINGLISH_MAP[clean_word]
        elif clean_word:
            # Character-by-character transliteration for unknown words
            hinglish_word = ''
            i = 0
            while i < len(clean_word):
                # Try 2-character combinations first (for matras)
                if i + 1 < len(clean_word):
                    two_char = clean_word[i:i+2]
                    if two_char in CHAR_MAP:
                        hinglish_word += CHAR_MAP[two_char]
                        i += 2
                        continue
                
                # Single character
                char = clean_word[i]
                if char in CHAR_MAP:
                    hinglish_word += CHAR_MAP[char]
                else:
                    hinglish_word += char
                i += 1
            
            # Clean up double vowels (simplified)
            hinglish_word = re.sub(r'aa+', 'aa', hinglish_word)
            hinglish_word = re.sub(r'ee+', 'ee', hinglish_word)
            hinglish_word = re.sub(r'oo+', 'oo', hinglish_word)
        else:
            hinglish_word = clean_word
        
        # Add back punctuation
        hinglish_words.append(hinglish_word + punctuation)
    
    result = ' '.join(hinglish_words)
    
    # Capitalize first letter
    if result:
        result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()
    
    return result


def generate_hindi_question_variants(english_questions, hindi_answer):
    """Generate additional Hindi question variants based on English questions."""
    hindi_variants = []
    
    # Common Hindi question patterns
    question_templates = {
        'What is': 'क्या है',
        'How to': 'कैसे करें',
        'Who can': 'कौन कर सकता',
        'When': 'कब',
        'Where': 'कहाँ',
        'Why': 'क्यों',
        'How many': 'कितने',
        'How much': 'कितना',
        'Is': 'क्या',
        'Are': 'क्या',
        'Can': 'क्या कर सकते',
        'What are': 'क्या हैं',
        'Explain': 'समझाएं',
        'Describe': 'वर्णन करें',
        'Tell me': 'बताएं',
    }
    
    for en_q in english_questions[:3]:  # Use first 3 English questions as base
        # Add the existing Hindi question pattern
        hindi_q = f"हिंदी प्रश्न {len(hindi_variants) + 1}"  # Placeholder
        
        # Create variations based on common patterns
        if 'What' in en_q:
            hindi_variants.append(en_q.replace('What', 'क्या'))
        elif 'How' in en_q:
            hindi_variants.append(en_q.replace('How', 'कैसे'))
        else:
            hindi_variants.append(en_q)
    
    return hindi_variants[:3]  # Return 3 variants


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
    
    # Generate Hindi question variants based on English questions
    # Use patterns from English questions but keep them in Hindi
    new_hindi_questions = list(hi_questions)  # Start with existing
    
    # Create variations based on common Hindi patterns
    for en_q in en_questions:
        if len(new_hindi_questions) >= 3:
            break
        
        # Simple translation patterns
        translations = {
            'What is': 'क्या है',
            'How to': 'कैसे करें',
            'How can': 'कैसे कर सकते',
            'Who can': 'कौन कर सकता',
            'When': 'कब',
            'Where': 'कहाँ',
            'Why': 'क्यों',
            'How many': 'कितने',
            'How much': 'कितना',
            'Is': 'क्या',
            'Are': 'क्या',
            'Can': 'क्या कर सकते',
            'What are': 'क्या हैं',
            'Explain': 'समझाएं',
            'Describe': 'वर्णन करें',
            'Tell': 'बताएं',
            'What happens': 'क्या होता है',
            'What if': 'क्या होगा यदि',
            'Do I': 'क्या मुझे',
            'Should I': 'क्या मुझे',
            'Must I': 'क्या मुझे',
            'Will I': 'क्या मुझे',
        }
        
        hi_q = en_q
        for en_pattern, hi_pattern in translations.items():
            if en_q.startswith(en_pattern):
                hi_q = en_q.replace(en_pattern, hi_pattern)
                break
        
        # Avoid duplicates
        if hi_q not in new_hindi_questions:
            new_hindi_questions.append(hi_q)
    
    # Update Hindi variant with new questions
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
    
    # Common English to Hinglish conversions
    hinglish_mappings = {
        'What is': 'Kya hai',
        'How to': 'Kaise karein',
        'How can': 'Kaise kar sakte',
        'Who can': 'Kaun kar sakta',
        'When': 'Kab',
        'Where': 'Kahan',
        'Why': 'Kyun',
        'How many': 'Kitne',
        'How much': 'Kitna',
        'Is': 'Kya',
        'Are': 'Kya',
        'Can': 'Kya kar sakte',
        'What are': 'Kya hain',
        'Explain': 'Samjhayein',
        'Describe': 'Vivaran karein',
        'Tell': 'Batayein',
        'What happens': 'Kya hota hai',
        'What if': 'Agar toh',
        'Do I': 'Kya mujhe',
        'Should I': 'Kya mujhe',
        'Must I': 'Kya mujhe',
        'Will I': 'Kya mujhe',
        'admission': 'admission',
        'process': 'process',
        'online': 'online',
        'registration': 'registration',
        'form': 'form',
        'college': 'college',
        'fee': 'fee',
        'payment': 'payment',
        'document': 'document',
        'certificate': 'certificate',
        'eligibility': 'eligibility',
        'criteria': 'criteria',
        'round': 'round',
        'seat': 'seat',
        'quota': 'quota',
        'reservation': 'reservation',
    }
    
    for en_q in en_questions:
        if len(new_hinglish_questions) >= 4:
            break
        
        # Convert English question to Hinglish
        hinglish_q = en_q
        for en_word, hi_word in hinglish_mappings.items():
            hinglish_q = hinglish_q.replace(en_word, hi_word)
        
        # Capitalize first letter of each word for consistency
        hinglish_q = ' '.join([
            word[0].upper() + word[1:] if word else word
            for word in hinglish_q.split()
        ])
        
        # Avoid duplicates
        if hinglish_q not in new_hinglish_questions:
            new_hinglish_questions.append(hinglish_q)
    
    # Update Hinglish variant with new questions
    hinglish_variant['questions'] = new_hinglish_questions[:4]
    return True


def convert_hinglish_answers(item):
    """Convert Hinglish answers from Devanagari to Romanized script."""
    variants = item.get('variants', [])
    
    # Find Hindi and Hinglish variants
    hi_variant = next((v for v in variants if v.get('lang') == 'hi'), None)
    hinglish_variant = next((v for v in variants if v.get('lang') == 'hinglish'), None)
    
    if not hi_variant or not hinglish_variant:
        return False
    
    hindi_answer = hi_variant.get('answer', '')
    current_hinglish_answer = hinglish_variant.get('answer', '')
    
    # Check if current Hinglish answer is in Devanagari script
    if not any('\u0900' <= char <= '\u097F' for char in current_hinglish_answer):
        return False  # Already in Roman script
    
    # Convert Hindi answer to Hinglish
    hinglish_answer = transliterate_hindi_to_hinglish(hindi_answer)
    
    if hinglish_answer and hinglish_answer != current_hinglish_answer:
        hinglish_variant['answer'] = hinglish_answer
        return True
    
    return False


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
        'hinglish_answers_converted': 0,
    }
    
    print(f"Processing {stats['total_entries']} FAQ entries...")
    
    for i, item in enumerate(data):
        # Enhance Hindi questions
        if enhance_hindi_questions(item):
            stats['hindi_questions_enhanced'] += 1
        
        # Enhance Hinglish questions
        if enhance_hinglish_questions(item):
            stats['hinglish_questions_enhanced'] += 1
        
        # Convert Hinglish answers to Romanized script
        if convert_hinglish_answers(item):
            stats['hinglish_answers_converted'] += 1
        
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
    print(f"Hinglish answers converted to Romanized: {stats['hinglish_answers_converted']} entries")
    print(f"\nOutput saved to: {output_path}")
    print("=" * 60)
    
    # Ask user if they want to replace the original
    print("\nTo replace the original file, run:")
    print(f"  mv {output_path} {json_path}")
    print("\nOr manually review and merge changes.")


if __name__ == "__main__":
    main()
