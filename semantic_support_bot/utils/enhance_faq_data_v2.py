#!/usr/bin/env python3
"""
Enhance FAQ JSON data with:
1. Additional Hindi question variants (currently only 1 per entry)
2. Convert Hinglish answers from Devanagari to Romanized script (manual mapping)
3. Improve Hinglish question coverage to 3+ per entry
"""

import json
import re
from pathlib import Path


# Comprehensive Hindi to Hinglish mapping (most common words in FAQ)
HINDI_TO_HINGLISH = {
    # Question words
    'क्या': 'kya', 'है': 'hai', 'हैं': 'hain', 'था': 'tha', 'थी': 'thi', 'थे': 'the',
    'कौन': 'kaun', 'कब': 'kab', 'कहाँ': 'kahan', 'क्यों': 'kyun', 'कैसे': 'kaise',
    'कितना': 'kitna', 'कितनी': 'kitni', 'कितने': 'kitne', 'किस': 'kis', 'किसने': 'kisne',
    
    # Pronouns
    'मैं': 'main', 'मुझे': 'mujhe', 'मेरा': 'mera', 'मेरी': 'meri', 'मेरे': 'mere',
    'तू': 'tu', 'तुझे': 'tujhe', 'तेरा': 'tera', 'तेरी': 'teri', 'तेरे': 'tere',
    'आप': 'aap', 'आपको': 'aapko', 'आपका': 'aapka', 'आपकी': 'aapki', 'आपके': 'aapke',
    'यह': 'yeh', 'यह': 'yah', 'इस': 'is', 'इसने': 'isne', 'इसे': 'ise',
    'वह': 'vah', 'वह': 'woh', 'उस': 'us', 'उसने': 'usne', 'उसे': 'use',
    'हम': 'hum', 'हमको': 'humko', 'हमारा': 'hamara', 'हमारी': 'hamari', 'हमारे': 'hamare',
    'ये': 'ye', 'वे': 've', 'उन': 'un', 'उनका': 'unka', 'उनकी': 'unki', 'उनके': 'unke',
    
    # Verbs (common forms)
    'करना': 'karna', 'करता': 'karta', 'करती': 'karti', 'करते': 'karte',
    'करूँ': 'karun', 'करे': 'kare', 'करें': 'karein', 'करो': 'karo',
    'कर सकता': 'kar sakta', 'कर सकती': 'kar sakti', 'कर सकते': 'kar sakte',
    'करना होगा': 'karna hoga', 'करनी होगी': 'karni hogi',
    'होता': 'hota', 'होती': 'hoti', 'होते': 'hote', 'होना': 'hona',
    'होगा': 'hoga', 'होगी': 'hogi', 'होंगे': 'honge',
    'जाता': 'jata', 'जाती': 'jati', 'जाते': 'jate', 'जाना': 'jana',
    'आता': 'aata', 'आती': 'aati', 'आते': 'aate', 'आना': 'aana',
    'देता': 'deta', 'देती': 'deti', 'देते': 'dete', 'देना': 'dena',
    'लेता': 'leta', 'लेती': 'leti', 'लेते': 'lete', 'लेना': 'lena',
    'पड़ता': 'padta', 'पड़ती': 'padti', 'पड़ते': 'padte', 'पड़ना': 'padna',
    'सकता': 'sakta', 'सकती': 'sakti', 'सकते': 'sakte',
    'चाहिए': 'chahiye', 'चाहता': 'chahta', 'चाहती': 'chahti', 'चाहते': 'chahte',
    'सकें': 'saken', 'सकूँ': 'sakun',
    
    # Common nouns (FAQ specific)
    'छात्र': 'chhatra', 'छात्रों': 'chatron', 'विद्यार्थी': 'vidyarthi',
    'प्रवेश': 'praves', 'एडमिशन': 'admission', 'कॉलेज': 'college',
    'स्कूल': 'school', 'विद्यालय': 'vidyalaya', 'कक्षा': 'kaksha',
    'फीस': 'fees', 'शुल्क': 'shulk', 'पेमेंट': 'payment', 'भुगतान': 'bhugtan',
    'रजिस्ट्रेशन': 'registration', 'पंजीकरण': 'panjikaran', 'नोंदणी': 'nodni',
    'फॉर्म': 'form', 'आवेदन': 'avedan', 'अर्ज': 'arj',
    'लॉगिन': 'login', 'पासवर्ड': 'password', 'आईडी': 'ID',
    'अकाउंट': 'account', 'खाता': 'khaata',
    'वेबसाइट': 'website', 'पोर्टल': 'portal', 'जालस्थल': 'jaalasthal',
    'लिंक': 'link', 'बटन': 'button', 'क्लिक': 'click',
    'सिलेक्ट': 'select', 'चयन': 'chayan', 'चुनें': 'chunen',
    'सबमिट': 'submit', 'जमा': 'jama', 'प्रस्तुत': 'prastut',
    'अपलोड': 'upload', 'डाउनलोड': 'download', 'प्रिंट': 'print',
    'चेक': 'check', 'जाँच': 'jaanch', 'सत्यापित': 'satyapit', 'वेरिफाई': 'verify',
    'अपडेट': 'update', 'एडिट': 'edit', 'संपादित': 'sampaadit',
    'डिलीट': 'delete', 'हटाएं': 'hataein', 'कैंसल': 'cancel',
    'कन्फर्म': 'confirm', 'पुष्टि': 'pushti', 'सेव': 'save', 'सहेजें': 'sahein',
    'नोटिफिकेशन': 'notification', 'सूचना': 'soochana', 'संदेश': 'sandesh',
    'मैसेज': 'message', 'एसएमएस': 'SMS', 'ईमेल': 'email',
    'फोन': 'phone', 'नंबर': 'number', 'संपर्क': 'sampark',
    'राउंड': 'round', 'फेरी': 'feri', 'सीट': 'seat', 'आसन': 'aasan',
    'अलॉटमेंट': 'allotment', 'आवंटन': 'aavantan', 'लिस्ट': 'list',
    'सूची': 'soochi', 'कैटेगरी': 'category', 'श्रेणी': 'shreni',
    'रिजर्वेशन': 'reservation', 'आरक्षण': 'aarakshan', 'कोटा': 'quota',
    'सर्टिफिकेट': 'certificate', 'प्रमाणपत्र': 'pramaanpatra',
    'दस्तावेज': 'dastavez', 'कागजात': 'kaagazaat',
    'मार्कशीट': 'marksheet', 'अंकपत्र': 'ankpatra', 'कार्ड': 'card',
    'बुकलेट': 'booklet', 'पुस्तिका': 'pustika',
    'गाइडलाइन': 'guideline', 'दिशानिर्देश': 'dishaanirdesh',
    'प्रोसेस': 'process', 'प्रक्रिया': 'prakriya',
    'स्टेप': 'step', 'चरण': 'charan', 'तरीका': 'tarika',
    'समस्या': 'samasya', 'दिक्कत': 'dikkat', 'परेशानी': 'pareshani',
    'शिकायत': 'shikayat', 'ग्रीवेंस': 'grievance',
    'हेल्प': 'help', 'सहायता': 'sahayata', 'मदद': 'madad',
    'समय': 'samay', 'तारीख': 'tareekh', 'दिन': 'din',
    'साल': 'saal', 'वर्ष': 'varsh', 'महीने': 'mahine',
    'घंटे': 'ghante', 'मिनट': 'minute', 'बजे': 'baje',
    'पहले': 'pehle', 'बाद': 'baad', 'during': 'ke dauran',
    'नया': 'naya', 'नई': 'nayi', 'नए': 'naye', 'पुराना': 'purana',
    'स्टूडेंट': 'student', 'टीचर': 'teacher', 'प्रोफेसर': 'professor',
    'क्लास': 'class', 'कोर्स': 'course', 'सब्जेक्ट': 'subject',
    'विषय': 'vishay', 'एग्जाम': 'exam', 'परीक्षा': 'pariksha',
    'टेस्ट': 'test', 'रिजल्ट': 'result', 'परिणाम': 'parinaam',
    'ग्रेड': 'grade', 'अंक': 'ank', 'रैंक': 'rank',
    'महाराष्ट्र': 'Maharashtra', 'राज्य': 'rajya', 'बोर्ड': 'board',
    'मंडळ': 'mandal', 'विभाग': 'vibhag', 'विज्ञान': 'vigyan',
    'कॉमर्स': 'commerce', 'वाणिज्य': 'vaanijya', 'आर्ट्स': 'arts',
    'कला': 'kala', 'स्ट्रीम': 'stream', 'शाखा': 'shakha',
    'अंग्रेजी': 'angrezi', 'हिंदी': 'hindi', 'मराठी': 'marathi',
    'गणित': 'ganit', 'सामान्य': 'samanya', 'जनरल': 'general',
    'ओबीसी': 'OBC', 'एससी': 'SC', 'एसटी': 'ST', 'ईडब्ल्यूएस': 'EWS',
    'आर्थिक': 'aarthik', 'कमजोर': 'kamzor', 'वर्ग': 'varg',
    'अभ्यर्थी': 'abhyarthi', 'उम्मीदवार': 'ummidwar', 'आवेदक': 'avedak',
    'घोषणा': 'ghoshna', 'प्रकाशित': 'prakashit', 'जारी': 'jaari',
    'निर्देश': 'nirdesh', 'नियम': 'niyam', 'शर्त': 'shart',
    'पात्रता': 'patrata', 'योग्यता': 'yogyata', 'मानदंड': 'mandand',
    'अनिवार्य': 'anivarya', 'जरूरी': 'zaroori', 'आवश्यक': 'aavashyak',
    'लागू': 'laagu', 'मान्य': 'manya', 'अमान्य': 'amanya',
    'स्वीकार': 'sweekar', 'मंजूरी': 'manjoori', 'अनुमति': 'anumati',
    'खारिज': 'khariz', 'रद्द': 'radd', 'सक्रिय': 'sakriya',
    'निष्क्रिय': 'nishkriya', 'चालू': 'chaalu', 'बंद': 'band',
    'शुरू': 'shuru', 'प्रारंभ': 'prarambh', 'समाप्त': 'samaapt',
    'पूरा': 'poora', 'पूर्ण': 'poorn', 'अधूरा': 'adhoora',
    'सफल': 'safal', 'विफल': 'vifal', 'सही': 'sahi',
    'गलत': 'galat', 'ठीक': 'theek', 'सही': 'sahi',
    
    # Conjunctions and particles
    'और': 'aur', 'या': 'ya', 'या': 'ya', 'लेकिन': 'lekin',
    'परंतु': 'parantu', 'मगर': 'magar', 'क्योंकि': 'kyunki',
    'अगर': 'agar', 'यदि': 'yadi', 'तो': 'to', 'तब': 'tab',
    'भी': 'bhi', 'ही': 'hi', 'से': 'se', 'तक': 'tak',
    'पर': 'par', 'में': 'mein', 'मैं': 'main', 'का': 'ka',
    'की': 'ki', 'के': 'ke', 'को': 'ko', 'लिए': 'liye',
    'साथ': 'saath', 'बिना': 'bina', 'तक': 'tak', 'ही': 'hi',
    
    # Numbers
    'एक': 'ek', 'दो': 'do', 'तीन': 'teen', 'चार': 'chaar',
    'पांच': 'paanch', 'छह': 'chah', 'सात': 'saat', 'आठ': 'aath',
    'नौ': 'nau', 'दस': 'das', 'सौ': 'sau', 'हजार': 'hazaar',
    
    # Miscellaneous
    'हाँ': 'haan', 'नहीं': 'nahin', 'ना': 'na', 'कभी': 'kabhi',
    'सब': 'sab', 'सभी': 'sabhi', 'कुछ': 'kuch', 'हर': 'har',
    'दूसरा': 'doosra', 'दूसरी': 'doosri', 'दूसरे': 'doosre',
    'पहला': 'pehla', 'पहली': 'pehli', 'पहले': 'pehle',
    'अगला': 'agla', 'अगली': 'agli', 'अगले': 'agle',
    'अंतिम': 'antim', 'आखिरी': 'aakhiri', 'फिर': 'phir',
    'अब': 'ab', 'अभी': 'abhi', 'जब': 'jab', 'तब': 'tab',
    'जहाँ': 'jahan', 'वहाँ': 'wahan', 'कहीं': 'kahin',
    'यहीं': 'yahin', 'वहीं': 'wahin', 'हर': 'har',
    
    # Special characters
    '।': '.', '॥': '.', '०': '0', '१': '1', '२': '2',
    '३': '3', '४': '4', '५': '5', '६': '6', '७': '7',
    '८': '8', '९': '9', '₹': 'Rs.',
    
    # Additional FAQ-specific words
    'संबद्ध': 'sambaddh', 'उच्च': 'uchch', 'माध्यमिक': 'madhyamik',
    'विद्यालयों': 'vidyalayon', 'कक्षा': 'kaksha', 'वीं': 'vin',
    'लिए': 'liye', 'इच्छुक': 'ichchhuk', 'छात्रों': 'chatron',
    'आवेदन': 'avedan', 'केंद्रीय': 'kendriya', 'प्रक्रिया': 'prakriya',
    'एक': 'ek', 'सुविधा': 'suvidha', 'वेब': 'web',
    'राज्य': 'rajya', 'बोर्ड': 'board', 'से': 'se',
    'महाराष्ट्र': 'Maharashtra', 'में': 'mein', 'और': 'aur',
    'प्रवेश': 'praves', 'हेतु': 'hetu', 'की': 'ki',
    'मान्यता': 'manyata', 'प्राप्त': 'prapt', 'उत्तीर्ण': 'uttirn',
    'किया': 'kiya', 'कक्षा': 'kaksha', 'चाहते': 'chahte',
    'वे': 've', 'इसके': 'iske', 'सकते': 'sakte',
    'ऑनलाइन': 'online', 'अनिवार्य': 'anivarya', 'है': 'hai',
    'ऑफलाइन': 'offline', 'जाएंगे': 'jayenge', 'नहीं': 'nahin',
    'किए': 'kiye', 'जाते': 'jate', 'समय': 'samay',
    'एसएमएस': 'SMS', 'के': 'ke', 'माध्यम': 'madhyam',
    'भेजी': 'bheji', 'जाएगी': 'jayegi', 'अपने': 'apne',
    'सुरक्षा': 'suraksha', 'प्रश्न': 'prashn', 'क्रेडेंशियल': 'credential',
    'संभाल': ' sambhal', 'कर': 'kar', 'रखें': 'rakhein',
    'पहले': 'pehle', 'बाद': 'baad', 'पुष्टि': 'pushti',
    'संपर्क': 'sampark', 'केंद्र': 'kendra', 'सुधार': 'sudhar',
    'सकता': 'sakta', 'हूं': 'hoon', 'थे': 'the',
    'दिया': 'diya', 'गया': 'gaya', 'गई': 'gayi',
    'गए': 'gaye', 'दिए': 'diye', 'लिया': 'liya',
    'लिये': 'liye', 'किया': 'kiya', 'किये': 'kiye',
    'कहीं': 'kahin', 'नहीं': 'nahin', 'यहीं': 'yahin',
}


def transliterate_hindi_to_hinglish(hindi_text):
    """Convert Hindi text in Devanagari to Hinglish (Romanized Hindi)."""
    if not hindi_text:
        return hindi_text
    
    # Check if text is in Devanagari
    if not any('\u0900' <= char <= '\u097F' for char in hindi_text):
        return hindi_text  # Already in Roman script
    
    # Tokenize and translate word by word
    # Preserve punctuation and spacing
    tokens = re.findall(r'[\u0900-\u097F]+|[^\u0900-\u097F]+', hindi_text)
    
    hinglish_tokens = []
    for token in tokens:
        if re.match(r'^[\u0900-\u097F]+$', token):
            # It's a Hindi word - translate it
            if token in HINDI_TO_HINGLISH:
                hinglish_tokens.append(HINDI_TO_HINGLISH[token])
            else:
                # Keep unknown words as-is (transliterate character by character)
                hinglish_tokens.append(token)
        else:
            # It's punctuation, number, or English word - keep as-is
            hinglish_tokens.append(token)
    
    result = ''.join(hinglish_tokens)
    
    # Clean up multiple spaces
    result = re.sub(r'\s+', ' ', result)
    
    # Capitalize first letter
    if result and len(result) > 0:
        result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()
    
    return result


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
        return False  # Already in Roman script (or was previously converted)
    
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
    
    print("\nTo replace the original file, run:")
    print(f"  mv {output_path} {json_path}")


if __name__ == "__main__":
    main()
