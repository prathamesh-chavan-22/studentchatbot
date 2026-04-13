import requests
import json

def test_chat(query, expected_lang=None):
    url = "http://localhost:8001/api/chat"
    payload = {"message": query, "history": []}
    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        print(f"\nQuery: '{query}'")
        print(f"Detected Lang: {data.get('detected_lang')}")
        print(f"Match ID: {data.get('match_id')}")
        print(f"Answer: {data.get('answer')[:150]}...") # Truncated for readability
        
    except Exception as e:
        print(f"Error testing query '{query}': {e}")

if __name__ == "__main__":
    print("Verifying Extended Multilingual Knowledge Base (48 FAQs)...")
    
    # Test specific topics from the new data
    test_chat("What is Zero Round?", expected_lang="en") # FAQ 26
    test_chat("शून्य फेरी म्हणजे काय?", expected_lang="mr") # FAQ 26
    test_chat("ज़ीरो राउंड क्या है?", expected_lang="hi") # FAQ 26
    
    test_chat("ATKT rules for science", expected_lang="en") # FAQ 9
    test_chat("आयसीएसई मंडळाचे गुण कसे नोंदवावे?", expected_lang="mr") # FAQ 46
    test_chat("क्या मैं अपना प्रवेश रद्द कर सकता हूँ?", expected_lang="hi") # FAQ 36
    
    # Test a tricky/short one
    test_chat("ICSE marks", expected_lang="en")
