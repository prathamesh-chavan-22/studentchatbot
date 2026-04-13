#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add parent directory to path to import app.bot
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.bot import SimilarityBot

console = Console()

def test_thresholds():
    console.print("\n[bold blue]Starting Threshold and Fallback Tests...[/bold blue]\n")
    
    # Initialize bot with a specific threshold for testing
    # Using 0.80 for testing to see if slightly off queries trigger fallback
    threshold = 0.80
    bot = SimilarityBot(threshold=threshold)
    
    test_cases = [
        {
            "name": "High Similarity Match (English)",
            "query": "What is FYJC?",
            "expected_match": True,
            "lang": "en"
        },
        {
            "name": "Below Threshold Match (English)",
            "query": "Can you tell me about the admission fee for engineering?", # Not in KB
            "expected_match": False,
            "lang": "en"
        },
        {
            "name": "Below Threshold Match (Marathi)",
            "query": "पुण्यातील हवामान कसे आहे?", # Irrelevant (Weather in Pune)
            "expected_match": False,
            "lang": "mr"
        },
        {
            "name": "Below Threshold Match (Hinglish)",
            "query": "Bhai aaj cricket match kitne baje hai?", # Irrelevant (Cricket)
            "expected_match": False,
            "lang": "hinglish"
        }
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test Case", style="cyan")
    table.add_column("Query", style="white")
    table.add_column("Score", style="yellow")
    table.add_column("Match?", style="bold")
    table.add_column("Top Match", style="magenta")
    table.add_column("Response Type", style="blue")
    
    all_passed = True
    
    for case in test_cases:
        result = bot.answer(case["query"])
        score = result["score"]
        match_id = result.get("match_id")
        is_match = match_id is not None
        
        # Get actual top match for debugging if needed
        top_matches = bot.get_top_matches(case["query"], top_k=1)
        top_q = top_matches[0]["question"] if top_matches else "N/A"
        top_id = top_matches[0]["id"] if top_matches else "N/A"

        # Check if the result matches our expectation
        passed = (is_match == case["expected_match"])
        if not passed:
            all_passed = False
        
        # Verify fallback message if it was not a match
        response_type = "Answer" if is_match else "Fallback"
        if not is_match:
            # Check if fallback is localized
            fallback_msg = bot._get_unmatched_answer(result["detected_lang"])
            if result["answer"] != fallback_msg:
                response_type = "Incorrect Fallback!"
                all_passed = False
        
        status_color = "green" if passed else "red"
        match_status = f"[{status_color}]{'YES' if is_match else 'NO'}[/]"
        
        table.add_row(
            case["name"],
            case["query"][:30],
            f"{score:.4f}",
            match_status,
            f"{top_id} ({top_q[:20]}...)",
            response_type
        )
    
    console.print(table)
    
    if all_passed:
        console.print("\n[bold green]✅ All threshold tests passed successfully![/bold green]\n")
    else:
        console.print("\n[bold red]❌ Some threshold tests failed. Check the table above.[/bold red]\n")
        sys.exit(1)

if __name__ == "__main__":
    test_thresholds()
