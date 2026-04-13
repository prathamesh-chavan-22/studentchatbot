import json
import random

def generate_scenarios(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenarios = []
    
    # 1. Exact matches from the Knowledge Base (40 scenarios)
    count = 0
    while count < 40:
        faq = random.choice(data)
        variant = random.choice(faq['variants'])
        if not variant['questions']:
            continue
        question = random.choice(variant['questions'])
        scenarios.append({
            "id": f"exact_{count+1}",
            "type": "exact",
            "query": question,
            "expected_keywords": variant['answer'][:50], # Just checking if it starts with similar text
            "lang": variant['lang']
        })
        count += 1

    # 2. Paraphrased/Varied questions (30 scenarios)
    prefixes = ["Can you tell me ", "Please explain ", "I want to know ", "Tell me about ", "How does it work: "]
    count = 0
    while count < 30:
        faq = random.choice(data)
        variant = random.choice(faq['variants'])
        if variant['lang'] != 'en': # Stick to English for prefixes for simplicity in this script
            continue
        question = random.choice(variant['questions'])
        paraphrased = random.choice(prefixes) + question.lower()
        scenarios.append({
            "id": f"paraphrase_{count+1}",
            "type": "paraphrase",
            "query": paraphrased,
            "expected_keywords": variant['answer'][:30],
            "lang": variant['lang']
        })
        count += 1

    # 3. Out-of-scope/Irrelevant queries (15 scenarios)
    irrelevant = [
        "What is the weather today?",
        "Tell me a joke",
        "Who is the president of USA?",
        "How to bake a cake?",
        "What is 2+2?",
        "Where can I buy shoes?",
        "Is it raining in Mumbai?",
        "Best movies in 2024",
        "How to play cricket?",
        "Translate 'Hello' to French",
        "Stock market status",
        "IPL scores",
        "Latest news",
        "Good morning",
        "What is your name?"
    ]
    for i, q in enumerate(irrelevant):
        scenarios.append({
            "id": f"irrelevant_{i+1}",
            "type": "out_of_scope",
            "query": q,
            "expected_fallback": True,
            "lang": "en"
        })

    # 4. TYPO-heavy queries (10 scenarios)
    typo_variants = [
        ("admisoin process", "admission"),
        ("colleg preference", "preference"),
        ("registrasion fee", "registration"),
        ("how to aplic", "apply"),
        ("eligibilty for 11th", "eligibility"),
        ("doucmnt requried", "document"),
        ("forget pasword", "forgot password"),
        ("how many rond", "round"),
        ("quota seet", "quota"),
        ("onlin registr", "online registration")
    ]
    for i, (q, keyword) in enumerate(typo_variants):
        scenarios.append({
            "id": f"typo_{i+1}",
            "type": "typo",
            "query": q,
            "expected_keywords": keyword,
            "lang": "en"
        })

    # 5. Short/One-word queries (5 scenarios)
    shorts = ["Admission", "Fee", "College", "Documents", "Help"]
    for i, q in enumerate(shorts):
        scenarios.append({
            "id": f"short_{i+1}",
            "type": "short",
            "query": q,
            "expected_keywords": q.lower(),
            "lang": "en"
        })

    # Shuffle and pick top 100
    random.shuffle(scenarios)
    scenarios = scenarios[:100]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scenarios, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(scenarios)} scenarios in {output_path}")

if __name__ == "__main__":
    generate_scenarios("questions_answers.json", "test_scenarios.json")
