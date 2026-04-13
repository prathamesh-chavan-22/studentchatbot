import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat(message, history=None):
    url = f"{BASE_URL}/api/chat"
    payload = {"message": message, "history": history or []}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "text": response.text}

def print_result(query, result):
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    print(f"Answer: {result.get('answer', 'N/A')}")
    print(f"\nUsed Groq: {result.get('used_groq', 'N/A')}")
    if 'usage' in result:
        usage = result['usage']
        print(f"Tokens: {usage.get('total_tokens', 'N/A')} (Prompt: {usage.get('prompt_tokens')}, Completion: {usage.get('completion_tokens')})")
        print(f"Cost: ${usage.get('cost_usd', 'N/A')}")
    print(f"Sources: {len(result.get('sources', []))} retrieved")
    print(f"{'='*80}")

# Test cases covering different scenarios
test_cases = [
    # NEW entries you added - Application lock issues
    ("माझा अर्ज भरण्याची प्रक्रिया पूर्ण झाली असताना देखील, अर्ज पूर्ण झालेला नाही असे दर्शविले जाते किंवा लॉक करताना त्रुटी येते", "Marathi - App lock issue"),
    
    # NEW entries - College selection issues
    ("मी अनेक कॉलेजे निवडण्याचा प्रयत्न करतो आहे, पण वेबसाइट मला परवानगी देत नाही", "Marathi - College selection"),
    
    # NEW entries - Part 2 access
    ("After locking Part 1 of the application form, I am unable to view or access Part 2", "English - Part 2 access"),
    
    # NEW entries - College duplication
    ("While selecting multiple college preferences, the first selected college is being duplicated in the list", "English - College duplication"),
    
    # Existing Marathi queries
    ("FYJC माहिती पुस्तिका कोठून डाउनलोड करायची?", "Marathi - Download brochure"),
    
    # Existing English queries
    ("What is the procedure for FYJC admission?", "English - General procedure"),
    
    # Payment issues
    ("I have made a payment, but it is not reflecting on the website", "English - Payment issue"),
    
    # Technical issues
    ("I am facing technical issues such as errors, missing selections, or data not found", "English - Technical error"),
    
    # Out-of-scope (Guardrail test)
    ("Who is the Prime Minister of India?", "Out-of-scope - Should refuse"),
    
    # Greeting test
    ("Hello", "Greeting test"),
    
    # Edge Cases
    ("", "Empty query"),
    ("A" * 600, "Long query (>500 chars)"),
]

if __name__ == "__main__":
    print("🤖 Testing FYJC Support Bot with gpt-oss-20b model")
    print("Starting test suite...\n")
    
    # Check if server is running
    try:
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code != 200:
            print("❌ Server is not running. Please start it with: python -m uvicorn app.main:app --reload")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start it with: python -m uvicorn app.main:app --reload")
        exit(1)
    
    success_count = 0
    fail_count = 0
    
    for i, (query, description) in enumerate(test_cases, 1):
        print(f"\n\n📝 Test {i}/{len(test_cases)}: {description}")
        print(f"{'-'*80}")
        
        start_time = time.time()
        result = test_chat(query)
        elapsed = time.time() - start_time
        
        if 'error' in result:
            print(f"❌ FAILED: {result}")
            fail_count += 1
        else:
            print_result(query, result)
            success_count += 1
            print(f"⏱️  Response time: {elapsed:.2f}s")
        
        # Small delay to avoid overwhelming the API
        time.sleep(1)
    
    print(f"\n\n{'='*80}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total: {len(test_cases)}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"{'='*80}")
