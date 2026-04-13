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
        print(f"Answer: {data.get('answer')}")
        
        if expected_lang and data.get('detected_lang') != expected_lang:
            print(f"Warning: Expected language {expected_lang}, but got {data.get('detected_lang')}")
            
    except Exception as e:
        print(f"Error testing query '{query}': {e}")

if __name__ == "__main__":
    print("Testing Multilingual Support Bot...")
    
    # 1. English
    test_chat("What is FYJC?", expected_lang="en")
    
    # 2. Marathi
    test_chat("नोंदणी कशी करावी?", expected_lang="mr")
    
    # 3. Hindi
    test_chat("पंजीकरण कैसे करें?", expected_lang="hi")
    
    # 4. English -> Marathi mapping test (conceptual match)
    # If I ask in English about registration, it should still match faq_2
    test_chat("How to register?", expected_lang="en")
    
    # 5. Mixed/Ambiguous
    test_chat("FYJC kya hai?", expected_lang="hi") # Should detect Hindi
    test_chat("FYJC mhanje kay?", expected_lang="mr") # Should detect Marathi
