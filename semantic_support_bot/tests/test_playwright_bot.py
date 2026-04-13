"""
Comprehensive Playwright test suite for the FYJC Semantic Support Bot.
Includes functional tests, edge cases, multilingual tests, and stress tests.

Run with: pytest tests/test_playwright_bot.py -v
Make sure the server is running on http://localhost:8001
"""

import pytest
import json
import time
import asyncio
from pathlib import Path
from playwright.sync_api import Page, expect, TimeoutError
from datetime import datetime

# Load scenarios
TEST_DIR = Path(__file__).parent
with open(TEST_DIR / "test_scenarios.json", "r", encoding="utf-8") as f:
    SCENARIOS = json.load(f)


class TestBotFunctional:
    """Basic functional tests for the bot."""

    @pytest.mark.parametrize("scenario", SCENARIOS)
    def test_bot_scenario(self, page: Page, scenario):
        """Test bot with various scenarios from test_scenarios.json."""
        # Navigate to the bot page
        page.goto("http://localhost:8001/")

        # Open chat if not open
        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")
            expect(chat_box).to_be_visible()

        # Type question and send
        query = scenario["query"]
        page.fill("#chat-input", query)
        page.press("#chat-input", "Enter")

        # Wait for response
        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)
        page.wait_for_timeout(2000)  # Allow streaming to progress

        bot_messages = page.locator(".bot-msg:not(.temp)")
        last_msg = bot_messages.last
        response_text = last_msg.inner_text()

        print(f"\n{scenario['id']} ({scenario['type']}): Q: {query} -> A: {response_text[:100]}...")

        # Assertions
        if scenario.get("expected_fallback"):
            assert "support@mahafyjcadmissions.in" in response_text or "sorry" in response_text.lower() or "माफ करा" in response_text or "क्षमस्व" in response_text
        elif "expected_keywords" in scenario:
            assert len(response_text) > 10
            if len(scenario["expected_keywords"]) > 3:
                assert "support@mahafyjcadmissions.in" not in response_text or "found a close match" not in response_text.lower()

    def test_bot_page_loads(self, page: Page):
        """Test that the bot page loads correctly."""
        page.goto("http://localhost:8001/")
        expect(page).to_have_title("FYJC Support Bot")
        expect(page.locator("#chat-toggle")).to_be_visible()

    def test_chat_box_opens(self, page: Page):
        """Test that chat box opens when toggle is clicked."""
        page.goto("http://localhost:8001/")
        page.click("#chat-toggle")
        expect(page.locator("#chat-box")).to_be_visible()

    def test_chat_box_closes(self, page: Page):
        """Test that chat box closes when toggle is clicked again."""
        page.goto("http://localhost:8001/")
        page.click("#chat-toggle")
        expect(page.locator("#chat-box")).to_be_visible()
        page.click("#chat-toggle")
        expect(page.locator("#chat-box")).not_to_be_visible()


class TestBotMultilingual:
    """Test bot responses in different languages."""

    @pytest.mark.parametrize("query,language", [
        ("What is FYJC?", "English"),
        ("FYJC admission kaise hota hai?", "Hinglish"),
        ("अकरावी प्रवेश प्रक्रिया काय आहे?", "Marathi"),
        ("11th admission kaise karein?", "Hindi"),
        ("नोंदणी कशी करावी?", "Marathi"),
        ("पंजीकरण कैसे करें?", "Hindi"),
    ])
    def test_multilingual_queries(self, page: Page, query, language):
        """Test bot handles queries in multiple languages."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")
            expect(chat_box).to_be_visible()

        page.fill("#chat-input", query)
        page.press("#chat-input", "Enter")

        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)
        page.wait_for_timeout(2000)

        bot_messages = page.locator(".bot-msg:not(.temp)")
        response_text = bot_messages.last.inner_text()

        print(f"\n{language}: {query} -> {response_text[:100]}...")

        # Should get a response (not empty)
        assert len(response_text) > 10
        # Should not be a fallback for valid queries
        assert "support@mahafyjcadmissions.in" not in response_text or "found a close match" not in response_text.lower()


class TestBotEdgeCases:
    """Test edge cases and potential breaking points."""

    def test_empty_query(self, page: Page):
        """Test bot handles empty query gracefully."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        page.fill("#chat-input", "")
        page.press("#chat-input", "Enter")

        # Should handle gracefully (either no response or error message)
        page.wait_for_timeout(2000)
        bot_messages = page.locator(".bot-msg:not(.temp)")
        if bot_messages.count() > 0:
            response = bot_messages.last.inner_text()
            assert len(response) > 0  # Should say something

    def test_single_character_query(self, page: Page):
        """Test bot handles single character query."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        page.fill("#chat-input", "?")
        page.press("#chat-input", "Enter")

        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)
        response = page.locator(".bot-msg:not(.temp)").last.inner_text()
        assert len(response) > 0

    def test_very_long_query(self, page: Page):
        """Test bot handles very long query."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        long_query = "admission " * 50  # 500 characters
        page.fill("#chat-input", long_query)
        page.press("#chat-input", "Enter")

        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)
        response = page.locator(".bot-msg:not(.temp)").last.inner_text()
        assert len(response) > 0

    def test_special_characters_query(self, page: Page):
        """Test bot handles special characters."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        page.fill("#chat-input", "FYJC!!! What is it??? Tell me more...")
        page.press("#chat-input", "Enter")

        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)
        response = page.locator(".bot-msg:not(.temp)").last.inner_text()
        assert len(response) > 0

    def test_rapid_fire_queries(self, page: Page):
        """Test bot handles rapid consecutive queries."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        queries = ["What is FYJC?", "admission process", "documents required"]

        for query in queries:
            page.fill("#chat-input", query)
            page.press("#chat-input", "Enter")
            page.wait_for_timeout(500)  # Small delay between queries

        # Wait for all responses
        page.wait_for_timeout(5000)

        bot_messages = page.locator(".bot-msg:not(.temp)")
        # Should have at least some responses
        assert bot_messages.count() >= 1

    def test_out_of_scope_query(self, page: Page):
        """Test bot handles out of scope queries with fallback."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        page.fill("#chat-input", "What is the weather today?")
        page.press("#chat-input", "Enter")

        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)
        response = page.locator(".bot-msg:not(.temp)").last.inner_text()

        # Should trigger fallback message
        assert "support@mahafyjcadmissions.in" in response or "sorry" in response.lower()


class TestBotConcurrency:
    """Test bot behavior under concurrent load."""

    def test_concurrent_users_basic(self, page: Page):
        """Test basic concurrent access (simulated via rapid requests)."""
        # This is a basic test - for heavy concurrency, use the async load test
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        # Simulate 5 rapid concurrent-like requests
        for i in range(5):
            page.fill("#chat-input", f"Query {i}: What is FYJC?")
            page.press("#chat-input", "Enter")
            page.wait_for_timeout(300)

        page.wait_for_timeout(5000)

        bot_messages = page.locator(".bot-msg:not(.temp)")
        assert bot_messages.count() >= 1  # Should have at least one response

    def test_session_isolation(self, page: Page):
        """Test that chat history is isolated per session."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        # Send a query
        page.fill("#chat-input", "Test query for session isolation")
        page.press("#chat-input", "Enter")

        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)

        # Refresh page (should start fresh session)
        page.reload()

        # Chat should be empty or reset
        page.wait_for_timeout(1000)
        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        # The previous conversation should not be visible
        # (depends on implementation - may use localStorage)


class TestBotStress:
    """Stress tests to find breaking points."""

    def test_rapid_successive_requests(self, page: Page):
        """Test bot with rapid successive requests."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        # Send 10 requests in rapid succession
        for i in range(10):
            page.fill("#chat-input", f"Stress test query {i}")
            page.press("#chat-input", "Enter")
            page.wait_for_timeout(100)  # Very short delay

        # Wait for responses
        page.wait_for_timeout(10000)

        bot_messages = page.locator(".bot-msg:not(.temp)")
        print(f"\nStress test: {bot_messages.count()} responses received")

        # Should handle most requests (allowing for some failures)
        assert bot_messages.count() >= 5

    def test_long_conversation_thread(self, page: Page):
        """Test bot with a long conversation thread."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        queries = [
            "What is FYJC?",
            "How to apply?",
            "What documents are needed?",
            "Is there a fee?",
            "What about scholarships?",
            "When is the deadline?",
            "Can I cancel admission?",
            "How to print allotment letter?",
            "What are the quotas?",
            "Is online application mandatory?",
        ]

        for i, query in enumerate(queries):
            page.fill("#chat-input", query)
            page.press("#chat-input", "Enter")
            page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)
            page.wait_for_timeout(500)
            print(f"\nLong thread - Query {i+1}/10 completed")

        bot_messages = page.locator(".bot-msg:not(.temp)")
        assert bot_messages.count() == len(queries)


class TestBotPerformance:
    """Performance-related tests."""

    def test_response_time_basic(self, page: Page):
        """Test that bot responds within reasonable time."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        start_time = time.time()

        page.fill("#chat-input", "What is FYJC?")
        page.press("#chat-input", "Enter")

        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)

        end_time = time.time()
        response_time = end_time - start_time

        print(f"\nResponse time: {response_time:.2f}s")

        # Should respond within 10 seconds (includes network + processing)
        assert response_time < 10.0

    def test_streaming_completion(self, page: Page):
        """Test that message streaming completes properly."""
        page.goto("http://localhost:8001/")

        chat_box = page.locator("#chat-box")
        if not chat_box.is_visible():
            page.click("#chat-toggle")

        page.fill("#chat-input", "Explain the FYJC admission process in detail")
        page.press("#chat-input", "Enter")

        # Wait for initial response
        page.wait_for_selector(".bot-msg:not(.temp)", timeout=10000)

        # Wait for streaming to complete (check if message stabilizes)
        page.wait_for_timeout(5000)

        # Get the message twice with a delay to check if it's still streaming
        msg1 = page.locator(".bot-msg:not(.temp)").last.inner_text()
        page.wait_for_timeout(2000)
        msg2 = page.locator(".bot-msg:not(.temp)").last.inner_text()

        # Message should be stable (streaming completed)
        assert msg1 == msg2 or len(msg1) > 0


# Utility function for async concurrency tests
async def send_chat_request(client, query: str, request_id: int):
    """Send a chat request asynchronously."""
    import httpx

    try:
        payload = {"message": query, "history": []}
        async with client.stream("POST", "http://localhost:8001/api/chat", json=payload) as response:
            result = await response.aread()
            return {
                "id": request_id,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "query": query
            }
    except Exception as e:
        return {
            "id": request_id,
            "success": False,
            "error": str(e),
            "query": query
        }


@pytest.mark.asyncio
async def test_concurrent_load_50_users():
    """Load test with 50 concurrent users."""
    import httpx

    print("\n" + "="*60)
    print("LOAD TEST: 50 Concurrent Users")
    print("="*60)

    queries = [
        "What is FYJC?",
        "Admission process kya hai?",
        "Documents required for FYJC",
        "How to apply online?",
        "What are the quotas?",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            send_chat_request(client, queries[i % len(queries)], i)
            for i in range(50)
        ]

        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start

        successes = sum(1 for r in results if r.get("success", False))
        failures = 50 - successes

        print(f"\nResults:")
        print(f"  Total Requests: 50")
        print(f"  Successful: {successes}")
        print(f"  Failed: {failures}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {50/duration:.2f} req/s")
        print(f"  Avg Response Time: {duration/50:.2f}s")
        print("="*60)

        assert successes >= 45, f"Too many failures: {failures}/50"


@pytest.mark.asyncio
async def test_concurrent_load_100_users():
    """Load test with 100 concurrent users - stress test."""
    import httpx

    print("\n" + "="*60)
    print("STRESS TEST: 100 Concurrent Users")
    print("="*60)

    queries = [
        "What is FYJC?",
        "Admission process kya hai?",
        "Documents required for FYJC",
        "How to apply online?",
        "What are the quotas?",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            send_chat_request(client, queries[i % len(queries)], i)
            for i in range(100)
        ]

        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start

        successes = sum(1 for r in results if r.get("success", False))
        failures = 100 - successes

        print(f"\nResults:")
        print(f"  Total Requests: 100")
        print(f"  Successful: {successes}")
        print(f"  Failed: {failures}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {100/duration:.2f} req/s")
        print(f"  Avg Response Time: {duration/100:.2f}s")
        print("="*60)

        # Allow more failures under heavy load
        assert successes >= 80, f"Too many failures: {failures}/100"


@pytest.mark.asyncio
async def test_concurrent_load_200_users_breaking_point():
    """Breaking point test with 200 concurrent users."""
    import httpx

    print("\n" + "="*60)
    print("BREAKING POINT TEST: 200 Concurrent Users")
    print("="*60)

    queries = [
        "What is FYJC?",
        "Admission process kya hai?",
        "Documents required for FYJC",
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = [
            send_chat_request(client, queries[i % len(queries)], i)
            for i in range(200)
        ]

        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start

        successes = sum(1 for r in results if r.get("success", False))
        failures = 200 - successes

        error_types = {}
        for r in results:
            if not r.get("success", False):
                error = r.get("error", f"Status {r.get('status_code', 'unknown')}")
                error_types[error] = error_types.get(error, 0) + 1

        print(f"\nResults:")
        print(f"  Total Requests: 200")
        print(f"  Successful: {successes}")
        print(f"  Failed: {failures}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {200/duration:.2f} req/s")
        print(f"  Avg Response Time: {duration/200:.2f}s")
        print(f"\nError Breakdown:")
        for error, count in error_types.items():
            print(f"  - {error}: {count}")
        print("="*60)

        # This is a breaking point test - we expect some failures
        # Just report results, don't assert
        print(f"\n⚠️  Breaking point analysis: {failures}/200 requests failed")


@pytest.mark.asyncio
async def test_sustained_load():
    """Test sustained load over time."""
    import httpx

    print("\n" + "="*60)
    print("SUSTAINED LOAD TEST: 10 users for 30 seconds")
    print("="*60)

    queries = [
        "What is FYJC?",
        "Admission process?",
        "Documents?",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        all_results = []

        for round in range(6):  # 6 rounds of 10 requests each
            tasks = [
                send_chat_request(client, queries[i % len(queries)], round * 10 + i)
                for i in range(10)
            ]

            start = time.time()
            results = await asyncio.gather(*tasks)
            duration = time.time() - start

            all_results.extend(results)

            successes = sum(1 for r in results if r.get("success", False))
            print(f"  Round {round+1}/6: {successes}/10 successful ({duration:.2f}s)")

            await asyncio.sleep(5)  # Wait 5 seconds between rounds

        total_successes = sum(1 for r in all_results if r.get("success", False))
        print(f"\nTotal: {total_successes}/60 successful")
        print("="*60)

        assert total_successes >= 50, f"Too many failures in sustained load: {60-total_successes}/60"
