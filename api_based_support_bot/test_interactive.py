#!/usr/bin/env python3
"""
Interactive test script for FYJC Support Bot with gpt-oss-20b
Run this to test the bot interactively
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def check_server():
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def test_query(message, history=None):
    """Send a query to the bot"""
    url = f"{BASE_URL}/api/chat"
    payload = {"message": message, "history": history or []}
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "text": response.text}

def print_result(result):
    """Pretty print the result"""
    if 'error' in result:
        print(f"\n❌ ERROR: {result}")
        return
    
    print(f"\n{'='*80}")
    print(f"🤖 Answer:")
    print(f"{'='*80}")
    print(result.get('answer', 'N/A'))
    print(f"\n{'='*80}")
    print(f"📊 Stats:")
    print(f"  Used Groq: {result.get('used_groq', False)}")
    if 'usage' in result:
        usage = result['usage']
        print(f"  Tokens: {usage.get('total_tokens', 'N/A')}")
        print(f"  Cost: ${usage.get('cost_usd', 0):.6f}")
    print(f"  Sources: {len(result.get('sources', []))} retrieved")
    print(f"{'='*80}")

def main():
    print("\n" + "="*80)
    print("🤖 FYJC Support Bot - Interactive Test")
    print("   Model: openai/gpt-oss-20b")
    print("="*80)
    
    # Check if server is running
    if not check_server():
        print("\n❌ Server is not running!")
        print("   Please start it with: python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    print("\n✅ Server is running!")
    print("\n💡 Tips:")
    print("   - Type your question in Marathi or English")
    print("   - Type 'quit' or 'exit' to stop")
    print("   - Type 'test' to run predefined tests")
    print()
    
    history = []
    
    while True:
        try:
            query = input("You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == 'test':
                print("\n🧪 Running predefined tests...\n")
                test_queries = [
                    "माझा अर्ज भरण्याची प्रक्रिया पूर्ण झाली असताना देखील, अर्ज पूर्ण झालेला नाही",
                    "After locking Part 1, I can't access Part 2",
                    "I made a payment but it's not showing",
                    "Who is the Prime Minister?",
                    "Hello"
                ]
                
                for i, q in enumerate(test_queries, 1):
                    print(f"\n{'='*80}")
                    print(f"Test {i}/{len(test_queries)}: {q}")
                    print(f"{'='*80}")
                    result = test_query(q)
                    print_result(result)
                    print()
                
                continue
            
            result = test_query(query, history)
            print_result(result)
            
            # Update history
            history.append({"role": "user", "content": query})
            if 'answer' in result:
                history.append({"role": "bot", "content": result['answer']})
            # Keep only last 10 messages
            history = history[-10:]
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
