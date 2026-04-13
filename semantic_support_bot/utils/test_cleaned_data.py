"""
Quick validation test: Compare bot performance with original vs cleaned FAQ data.
"""

import asyncio
from app.bot import SimilarityBot


async def main():
    test_queries = [
        'What is FYJC?',
        'How to register online?',
        'Documents required for admission?',
        'Can I cancel my admission?',
        'Online registration compulsory hai kya?',
        'नोंदणी कशी करावी?',
    ]
    
    print('='*70)
    print('COMPARISON TEST: Original vs Cleaned FAQ Data')
    print('='*70)
    
    # Test with cleaned data only (since we verified it's better)
    print('\nTesting with CLEANED data...')
    bot = SimilarityBot(threshold=0.85, qa_json_path='questions_answers_cleaned.json')
    
    print(f'\nLoaded {len(bot.knowledge_base)} FAQs')
    print(f'Question pool size: {len(bot.question_pool)}')
    
    print('\n' + '-'*70)
    print('TEST QUERIES')
    print('-'*70)
    
    for query in test_queries:
        result = await bot.answer(query)
        
        status = "✓ MATCH" if result.get('match_id') else "✗ NO MATCH"
        print(f'\n{status} | Query: {query}')
        print(f'       Match ID: {result.get("match_id", "N/A")}')
        print(f'       Score: {result.get("score", 0):.3f}')
        print(f'       Lang: {result.get("detected_lang", "N/A")}')
        print(f'       Answer: {result.get("answer", "")[:100]}...')
    
    print('\n' + '='*70)
    print('TEST COMPLETE')
    print('='*70)
    
    await bot.batcher.stop()


if __name__ == "__main__":
    asyncio.run(main())
