"""
Pytest configuration and fixtures for FYJC Semantic Support Bot tests.
"""

import pytest
import httpx
import asyncio
from pathlib import Path


# Base URL for the API
BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for the API."""
    return BASE_URL


@pytest.fixture
async def async_client():
    """Provide an async HTTP client for API tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def sample_queries():
    """Return a list of sample test queries in different languages."""
    return [
        ("What is FYJC?", "en"),
        ("FYJC admission kaise hota hai?", "hinglish"),
        ("अकरावी प्रवेश प्रक्रिया काय आहे?", "mr"),
        ("11th admission kaise karein?", "hi"),
        ("What are the quota types?", "en"),
        ("Documents kya chahiye?", "hinglish"),
        ("How to print allotment letter?", "en"),
        ("Admission cancel kaise karein?", "hinglish"),
    ]


@pytest.fixture
def edge_case_queries():
    """Return edge case queries for testing."""
    return [
        ("", "empty"),
        ("?", "single_char"),
        ("admission", "single_word"),
        ("ADMISSION PROCESS", "all_caps"),
        ("  admission  process  ", "whitespace"),
        ("What is FYJC???", "special_chars"),
        ("admission " * 50, "long_query"),
        ("What is the weather?", "out_of_scope"),
    ]


@pytest.fixture
def load_test_configs():
    """Return load test configurations."""
    return {
        "light": {"users": 10, "timeout": 10.0},
        "medium": {"users": 50, "timeout": 30.0},
        "heavy": {"users": 100, "timeout": 60.0},
        "stress": {"users": 200, "timeout": 60.0},
    }


@pytest.fixture
def test_results_dir(tmp_path):
    """Create a temporary directory for test results."""
    results_dir = tmp_path / "test_results"
    results_dir.mkdir()
    return results_dir


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "load_test: marks tests as load tests"
    )


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--url",
        action="store",
        default=BASE_URL,
        help="Base URL of the server (default: http://localhost:8001)"
    )
    parser.addoption(
        "--slow-tests",
        action="store_true",
        default=False,
        help="Run slow tests"
    )


@pytest.hookimpl(tryfirst=True)
def pytest_cmdline_main(config):
    """Handle command line options."""
    if config.option.url:
        global BASE_URL
        BASE_URL = config.option.url
