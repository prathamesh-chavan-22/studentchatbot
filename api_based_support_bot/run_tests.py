import json
import requests
import time
from datetime import datetime

API_URL = "http://localhost:8000/api/chat"

def run_tests():
    with open("test_cases.json", "r") as f:
        test_cases = json.load(f)

    results = []
    print(f"Starting {len(test_cases)} test cases...")

    for test in test_cases:
        print(f"Running Test {test['id']}: {test['category']}")
        history = []
        test_results = {
            "id": test["id"],
            "category": test["category"],
            "turns": []
        }

        for turn in test["turns"]:
            payload = {
                "message": turn["message"],
                "history": history
            }
            
            start_time = time.time()
            try:
                response = requests.post(API_URL, json=payload, timeout=30)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    bot_answer = data.get("answer", "")
                    
                    # Check keywords
                    found_keywords = [kw for kw in turn["expected_keywords"] if kw.lower() in bot_answer.lower()]
                    success = len(found_keywords) > 0 or not turn["expected_keywords"]
                    
                    turn_result = {
                        "user_message": turn["message"],
                        "bot_answer": bot_answer,
                        "duration_sec": round(duration, 2),
                        "status": "PASS" if success else "FAIL",
                        "expected_keywords": turn["expected_keywords"],
                        "found_keywords": found_keywords
                    }
                    
                    # Update history for next turn
                    history.append({"role": "user", "content": turn["message"]})
                    history.append({"role": "bot", "content": bot_answer})
                else:
                    turn_result = {
                        "user_message": turn["message"],
                        "error": f"HTTP {response.status_code}",
                        "status": "ERROR"
                    }
            except Exception as e:
                turn_result = {
                    "user_message": turn["message"],
                    "error": str(e),
                    "status": "ERROR"
                }
            
            test_results["turns"].append(turn_result)

        results.append(test_results)

    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Done. Results saved to test_results.json")

if __name__ == "__main__":
    run_tests()
