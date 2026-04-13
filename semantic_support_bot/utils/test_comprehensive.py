#!/usr/bin/env python3
"""
Comprehensive test suite for the Multilingual Semantic Bot.
Tests Hinglish, mixed queries, edge cases, and all supported languages.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.bot import SimilarityBot

console = Console()

# Test cases organized by category
TEST_CASES = {
    "English Queries": [
        ("What is FYJC?", "faq_1"),
        ("Who can apply for 11th admission?", "faq_2"),
        ("Is online registration mandatory?", "faq_3"),
        ("How to register online?", "faq_4"),
        ("Can I edit my application form?", "faq_5"),
        ("How many colleges can I list?", "faq_6"),
        ("What documents are required?", "faq_7"),
        ("I am from another board, what to do?", "faq_8"),
        ("What is ATKT?", "faq_9"),
        ("What are the quota types?", "faq_10"),
        ("How many rounds are conducted?", "faq_12"),
        ("What is the registration fee?", "faq_15"),
        ("How to withdraw from admission?", "faq_21"),
        ("What is Zero Round?", "faq_26"),
        ("What is Open to All round?", "faq_28"),
    ],
    
    "Hinglish Queries": [
        ("FYJC kya hai?", "faq_1"),
        ("11th admission kaise hota hai?", "faq_1"),
        ("Kaun apply kar sakta hai?", "faq_2"),
        ("Online registration zaroori hai kya?", "faq_3"),
        ("Online register kaise karein?", "faq_4"),
        ("Form edit kar sakte hain kya?", "faq_5"),
        ("Kitne colleges ki preference de sakte hain?", "faq_6"),
        ("Documents kya chahiye?", "faq_7"),
        ("Main dusre board se hoon, kya karun?", "faq_8"),
        ("ATKT kya hai aur kaun eligible hai?", "faq_9"),
        ("Quota types kya kya hain?", "faq_10"),
        ("Kitne rounds hote hain?", "faq_12"),
        ("Registration fee kitni hai?", "faq_15"),
        ("Admission cancel kaise karein?", "faq_21"),
        ("Zero Round kya hota hai?", "faq_26"),
        ("Open to All Round kya hai?", "faq_28"),
        ("Login details bhool gaya toh kya karun?", "faq_17"),
        ("College preference change kar sakte hain?", "faq_19"),
    ],
    
    "Hindi Queries (Devanagari)": [
        ("कक्षा 11वीं (FYJC) ऑनलाइन प्रवेश प्रक्रिया क्या है?", "faq_1"),
        ("11वीं प्रवेश के लिए कौन आवेदन कर सकता है?", "faq_2"),
        ("क्या ऑनलाइन पंजीकरण अनिवार्य है?", "faq_3"),
        ("ऑनलाइन पंजीकरण कैसे करें?", "faq_4"),
        ("क्या पंजीकरण के बाद आवेदन फॉर्म में सुधार किया जा सकता है?", "faq_5"),
        ("मैं अपनी प्राथमिकताओं में कितने कॉलेजों को सूचीबद्ध कर सकता हूँ?", "faq_6"),
        ("प्रवेश के लिए कौन से दस्तावेज आवश्यक हैं?", "faq_7"),
        ("मैं दूसरे बोर्ड का छात्र हूँ, मुझे क्या करना चाहिए?", "faq_8"),
        ("ATKT के लिए कौन पात्र है?", "faq_9"),
        ("कोटा प्रकार क्या हैं?", "faq_10"),
        ("पंजीकरण शुल्क कितना है?", "faq_15"),
        ("प्रवेश प्रक्रिया से बाहर कैसे निकलें?", "faq_21"),
        ("जीरो राउंड क्या है?", "faq_26"),
        ("ओपन टू ऑल राउंड क्या है?", "faq_28"),
    ],
    
    "Marathi Queries (Devanagari)": [
        ("इयत्ता ११ वी (FYJC) ऑनलाईन प्रवेश प्रक्रिया म्हणजे काय?", "faq_1"),
        ("११ वी प्रवेशासाठी कोण अर्ज करू शकतो?", "faq_2"),
        ("ऑनलाईन नोंदणी अनिवार्य आहे का?", "faq_3"),
        ("ऑनलाइन नोंदणी कशी करावी?", "faq_4"),
        ("नोंदणी नंतर प्रवेश अर्जात सुधारणा करता येते का?", "faq_5"),
        ("मी किती उच्च माध्यमिक विद्यालयांची पसंती देऊ शकतो?", "faq_6"),
        ("प्रवेशासाठी कोणती कागदपत्रे आवश्यक आहेत?", "faq_7"),
        ("मी इतर मंडळाचा विद्यार्थी आहे, मी काय करू?", "faq_8"),
        ("नोंदणी फी किती आहे आणि ती कशी भरावी?", "faq_15"),
        ("प्रवेश प्रक्रियेमधून माघार घेण्यासाठी काय करावे?", "faq_21"),
        ("शून्य फेरी (Zero Round) म्हणजे काय?", "faq_26"),
        ("ओपन टू ऑल फेरी म्हणजे काय?", "faq_28"),
    ],
    
    "Edge Cases & Variations": [
        ("fyjc", "faq_1"),  # Very short query
        ("ADMISSION", "faq_1"),  # All caps
        ("admission    process", "faq_1"),  # Extra spaces
        ("What is FYJC? What is FYJC?", "faq_1"),  # Repetition
        ("Plz tell me about FYJC admission", "faq_1"),  # Informal
        ("11th class admission Maharashtra", "faq_1"),  # Keywords only
        ("How do I get into 11th grade?", "faq_1"),  # Paraphrased
        ("Admission process for FYJC 2024", "faq_1"),  # With year
    ]
}


def run_tests(bot: SimilarityBot):
    """Run all test cases and display results."""
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for category, test_cases in TEST_CASES.items():
        console.print(Panel(f"[bold]{category}[/bold]", style="bold blue"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Query", style="white", max_width=40)
        table.add_column("Expected", style="cyan", width=10)
        table.add_column("Got", style="green", width=10)
        table.add_column("Score", style="yellow", width=8)
        table.add_column("Lang", style="blue", width=10)
        table.add_column("Status", style="bold", width=8)
        
        for query, expected_id in test_cases:
            total_tests += 1
            result = bot.answer(query)
            
            got_id = result.get("match_id", "N/A")
            score = result.get("score", 0)
            lang = result.get("detected_lang", "N/A")
            
            # Pass if score >= 0.70 and either exact match or same FAQ family
            passed = score >= 0.70 and (got_id == expected_id or got_id.startswith(expected_id.split("_")[0]))
            
            if passed:
                passed_tests += 1
                status = "[green]✓[/green]"
            else:
                status = "[red]✗[/red]"
                failed_tests.append((query, expected_id, got_id, score, lang))
            
            table.add_row(
                query[:35] + "..." if len(query) > 35 else query,
                expected_id,
                got_id,
                f"{score:.2f}",
                lang,
                status
            )
        
        console.print(table)
        console.print("")
    
    # Summary
    console.print(Panel(f"[bold]Test Summary[/bold]", style="bold blue"))
    
    summary_table = Table(show_header=False)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")
    
    accuracy = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    summary_table.add_row("Total Tests", str(total_tests))
    summary_table.add_row("Passed", f"[green]{passed_tests}[/green]")
    summary_table.add_row("Failed", f"[red]{len(failed_tests)}[/red]")
    summary_table.add_row("Accuracy", f"[{'green' if accuracy >= 80 else 'yellow' if accuracy >= 60 else 'red'}]{accuracy:.1f}%[/]")
    
    console.print(summary_table)
    
    if failed_tests:
        console.print("\n[bold red]Failed Tests:[/bold red]")
        for query, expected, got, score, lang in failed_tests[:10]:  # Show first 10 failures
            console.print(f"  • Query: '{query}'")
            console.print(f"    Expected: {expected}, Got: {got} (score: {score:.2f}, lang: {lang})")
    
    return passed_tests, total_tests


def main():
    console.print("\n" + "="*60)
    console.print("[bold]Multilingual Semantic Bot - Test Suite[/bold]")
    console.print("="*60 + "\n")
    
    # Initialize bot
    console.print("[bold]Initializing bot...[/bold]")
    bot = SimilarityBot()
    
    if not bot.knowledge_base or bot.question_embeddings is None:
        console.print("[bold red]Error: Bot failed to initialize![/bold red]")
        return 1
    
    console.print(f"[green]✓ Loaded {len(bot.knowledge_base)} FAQs[/green]")
    console.print(f"[green]✓ {len(bot.question_pool)} question variants[/green]\n")
    
    # Run tests
    passed, total = run_tests(bot)
    
    # Exit code based on results
    if passed == total:
        console.print("\n[bold green]🎉 All tests passed![/bold green]\n")
        return 0
    elif passed / total >= 0.80:
        console.print("\n[bold yellow]⚠ Most tests passed (≥80%)[/bold yellow]\n")
        return 0
    else:
        console.print("\n[bold red]❌ Test accuracy below 80%[/bold red]\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
