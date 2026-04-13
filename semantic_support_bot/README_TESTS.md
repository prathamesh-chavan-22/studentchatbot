# FYJC Semantic Support Bot - Test Suite

Comprehensive test suite including functional tests, multilingual tests, edge cases, concurrency tests, and stress tests.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Concurrency Testing](#concurrency-testing)
- [Interpreting Results](#interpreting-results)

## Prerequisites

1. **Python 3.11+** required
2. **Server running** on `http://localhost:8001`
3. **Playwright browsers** installed

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# For Chromium only (faster)
playwright install chromium
```

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_playwright_bot.py         # Main test suite (Playwright E2E)
├── test_scenarios.json            # Test scenarios data
├── test_moderation.py             # Content moderation tests
├── load_test_concurrency.py       # Standalone concurrency tests
└── README_TESTS.md                # This file
```

## Running Tests

### All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with output
pytest tests/ -v -s
```

### Specific Test Files

```bash
# Playwright E2E tests
pytest tests/test_playwright_bot.py -v

# Moderation tests
pytest tests/test_moderation.py -v

# Concurrency tests (standalone)
python tests/load_test_concurrency.py 50
```

### By Test Class

```bash
# Functional tests
pytest tests/test_playwright_bot.py::TestBotFunctional -v

# Multilingual tests
pytest tests/test_playwright_bot.py::TestBotMultilingual -v

# Edge case tests
pytest tests/test_playwright_bot.py::TestBotEdgeCases -v

# Concurrency tests
pytest tests/test_playwright_bot.py::TestBotConcurrency -v

# Stress tests
pytest tests/test_playwright_bot.py::TestBotStress -v

# Performance tests
pytest tests/test_playwright_bot.py::TestBotPerformance -v
```

### By Marker

```bash
# Skip slow tests
pytest tests/ -v -m "not slow"

# Run only slow tests
pytest tests/ -v -m slow

# Run integration tests
pytest tests/ -v -m integration
```

### Specific Test Cases

```bash
# Run a single test
pytest tests/test_playwright_bot.py::TestBotFunctional::test_bot_page_loads -v

# Run tests matching a keyword
pytest tests/test_playwright_bot.py -k "multilingual" -v

# Run tests by scenario type
pytest tests/test_playwright_bot.py -k "tc_001 or tc_002" -v
```

## Test Categories

### 1. Functional Tests (`TestBotFunctional`)

Basic functionality tests:
- Page loading
- Chat box open/close
- 40 test scenarios covering:
  - Basic queries (English, Hinglish, Marathi, Hindi)
  - Quota-related queries
  - Document requirements
  - Eligibility criteria
  - Admission rounds
  - Allotment letters
  - Admission cancellation
  - Fallback scenarios

### 2. Multilingual Tests (`TestBotMultilingual`)

Tests for language support:
- English queries
- Hinglish queries
- Marathi queries
- Hindi queries

### 3. Edge Case Tests (`TestBotEdgeCases`)

Boundary and error handling:
- Empty queries
- Single character queries
- Very long queries (500 chars)
- Special characters
- Rapid-fire queries
- Out-of-scope queries

### 4. Concurrency Tests (`TestBotConcurrency`)

Concurrent access patterns:
- Basic concurrent users
- Session isolation
- Rapid successive requests

### 5. Stress Tests (`TestBotStress`)

Breaking point identification:
- 10 rapid successive requests
- Long conversation threads (10 messages)

### 6. Performance Tests (`TestBotPerformance`)

Performance metrics:
- Response time measurement
- Streaming completion verification

## Concurrency Testing

### Using Pytest (Integrated)

```bash
# Run concurrency tests from pytest
pytest tests/test_playwright_bot.py::TestBotConcurrency -v

# Run async load tests
pytest tests/test_playwright_bot.py::test_concurrent_load_50_users -v
pytest tests/test_playwright_bot.py::test_concurrent_load_100_users -v
pytest tests/test_playwright_bot.py::test_concurrent_load_200_users_breaking_point -v
pytest tests/test_playwright_bot.py::test_sustained_load -v
```

### Using Standalone Load Tester

```bash
# Basic load test (50 users)
python tests/load_test_concurrency.py 50

# Stress test suite (50, 100, 150, 200 users)
python tests/load_test_concurrency.py --stress

# Find breaking point (ramp-up test)
python tests/load_test_concurrency.py --breaking-point

# Sustained load test (10 users x 6 rounds)
python tests/load_test_concurrency.py --sustained

# Custom URL
python tests/load_test_concurrency.py 100 --url http://localhost:8001

# Save results to JSON
python tests/load_test_concurrency.py 50 --save
```

### Load Test Configurations

| Test Type | Users | Timeout | Purpose |
|-----------|-------|---------|---------|
| Light | 10 | 10s | Basic functionality under load |
| Medium | 50 | 30s | Normal operation load |
| Heavy | 100 | 60s | High load stress test |
| Stress | 200 | 60s | Breaking point identification |
| Sustained | 10x6 | 30s | Memory leak detection |
| Ramp-up | 10→300 | 30s | Find exact breaking point |

## Interpreting Results

### Test Output Example

```
======================================
  LOAD TEST RESULTS
======================================
  Timestamp:        2026-04-02T10:30:00
  Concurrent Users: 100
----------------------------------------------------------------------
  Total Requests:   100
  Successful:       95
  Failed:           5
  Success Rate:     95.0%
----------------------------------------------------------------------
  Total Duration:   15.23s
  Throughput:       6.24 req/s
----------------------------------------------------------------------
  Avg Latency:      2.45s
  Median Latency:   2.12s
  Min Latency:      0.85s
  Max Latency:      8.92s
  Std Dev:          1.23s
  P95 Latency:      4.56s
  P99 Latency:      6.78s
----------------------------------------------------------------------
  Error Breakdown:
    - Timeout: 3
    - HTTP 503: 2
----------------------------------------------------------------------
======================================
```

### Key Metrics

- **Success Rate**: Should be >90% for normal operation
- **Throughput**: Requests per second the system can handle
- **Avg Latency**: Average response time
- **P95/P99 Latency**: 95th/99th percentile response times (important for SLA)
- **Error Breakdown**: Types of failures encountered

### Breaking Point Indicators

⚠️ **Warning signs:**
- Success rate drops below 90%
- P99 latency exceeds 10s
- Timeout errors increase
- HTTP 503 (Service Unavailable) errors appear

🛑 **Breaking point reached:**
- Success rate below 50%
- Majority of requests timeout
- Server becomes unresponsive

### Performance Benchmarks

| Metric | Excellent | Good | Acceptable | Poor |
|--------|-----------|------|------------|------|
| Success Rate | >99% | 95-99% | 90-95% | <90% |
| Avg Latency | <1s | 1-3s | 3-5s | >5s |
| P95 Latency | <2s | 2-5s | 5-8s | >8s |
| Throughput | >20 req/s | 10-20 req/s | 5-10 req/s | <5 req/s |

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Start server
        run: |
          python -m uvicorn app.main:app &
          sleep 10
      
      - name: Run tests
        run: pytest tests/ -v --tb=short
      
      - name: Run load test
        run: python tests/load_test_concurrency.py 50
```

## Troubleshooting

### Common Issues

**1. Playwright browser not found:**
```bash
playwright install chromium
```

**2. Connection refused:**
- Ensure server is running: `python -m uvicorn app.main:app --port 8001`
- Check URL: `pytest tests/ --url http://localhost:8001`

**3. Timeout errors in load tests:**
- Increase timeout: Edit `timeout` parameter in test
- Server may be overloaded - reduce concurrent users

**4. Async test errors:**
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Run with asyncio mode
pytest tests/ --asyncio-mode=auto
```

## Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [httpx Documentation](https://www.python-httpx.org/)
