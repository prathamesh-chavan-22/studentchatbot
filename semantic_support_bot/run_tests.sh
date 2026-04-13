#!/usr/bin/env bash
# Test runner script for FYJC Semantic Support Bot
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
VERBOSITY="-v"
URL="http://localhost:8001"

# Help message
show_help() {
    cat << EOF
${BLUE}FYJC Semantic Support Bot - Test Runner${NC}

Usage: ./run_tests.sh [options]

Options:
  -h, --help              Show this help message
  -t, --type TYPE         Test type: all, functional, multilingual, edge, concurrency, stress, performance
  -q, --quiet             Quiet mode (minimal output)
  -u, --url URL           Server URL (default: http://localhost:8001)
  --start-server          Start the server before running tests
  --coverage              Run with coverage report

Examples:
  ./run_tests.sh                          # Run all tests
  ./run_tests.sh -t functional            # Run only functional tests
  ./run_tests.sh -t stress -q             # Run stress tests in quiet mode
  ./run_tests.sh --start-server -t all    # Start server and run all tests

Test Types:
  all           Run all tests (default)
  functional    Basic functional tests
  multilingual  Multilingual support tests
  edge          Edge case tests
  concurrency   Concurrency tests
  stress        Stress and breaking point tests
  performance   Performance tests
  load          Standalone load tests (50, 100, 200 users)

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -q|--quiet)
            VERBOSITY=""
            shift
            ;;
        -u|--url)
            URL="$2"
            shift 2
            ;;
        --start-server)
            START_SERVER=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
else
    echo -e "${YELLOW}Warning: Virtual environment not found${NC}"
fi

# Start server if requested
if [ "$START_SERVER" = true ]; then
    echo -e "${BLUE}Starting server...${NC}"
    python -m uvicorn app.main:app --port 8001 &
    SERVER_PID=$!
    echo -e "${YELLOW}Server started with PID: $SERVER_PID${NC}"
    echo -e "${YELLOW}Waiting for server to be ready...${NC}"
    sleep 5
    
    # Cleanup function
    cleanup() {
        echo -e "\n${YELLOW}Stopping server (PID: $SERVER_PID)...${NC}"
        kill $SERVER_PID 2>/dev/null || true
    }
    trap cleanup EXIT
fi

# Check if server is running
check_server() {
    if curl -s "$URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is running at $URL${NC}"
        return 0
    else
        echo -e "${RED}✗ Server is not running at $URL${NC}"
        echo -e "${YELLOW}Hint: Start the server with: python -m uvicorn app.main:app --port 8001${NC}"
        return 1
    fi
}

# Run tests based on type
run_tests() {
    case $TEST_TYPE in
        all)
            echo -e "${BLUE}Running all tests...${NC}"
            if [ "$COVERAGE" = true ]; then
                pytest tests/ $VERBOSITY --cov=app --cov-report=html
            else
                pytest tests/ $VERBOSITY
            fi
            ;;
        
        functional)
            echo -e "${BLUE}Running functional tests...${NC}"
            pytest tests/test_playwright_bot.py::TestBotFunctional $VERBOSITY --url $URL
            ;;
        
        multilingual)
            echo -e "${BLUE}Running multilingual tests...${NC}"
            pytest tests/test_playwright_bot.py::TestBotMultilingual $VERBOSITY --url $URL
            ;;
        
        edge)
            echo -e "${BLUE}Running edge case tests...${NC}"
            pytest tests/test_playwright_bot.py::TestBotEdgeCases $VERBOSITY --url $URL
            ;;
        
        concurrency)
            echo -e "${BLUE}Running concurrency tests...${NC}"
            pytest tests/test_playwright_bot.py::TestBotConcurrency $VERBOSITY --url $URL
            pytest tests/test_playwright_bot.py::test_concurrent_load_50_users $VERBOSITY
            ;;
        
        stress)
            echo -e "${BLUE}Running stress tests...${NC}"
            pytest tests/test_playwright_bot.py::TestBotStress $VERBOSITY --url $URL
            pytest tests/test_playwright_bot.py::test_concurrent_load_100_users $VERBOSITY
            pytest tests/test_playwright_bot.py::test_concurrent_load_200_users_breaking_point $VERBOSITY
            ;;
        
        performance)
            echo -e "${BLUE}Running performance tests...${NC}"
            pytest tests/test_playwright_bot.py::TestBotPerformance $VERBOSITY --url $URL
            ;;
        
        load)
            echo -e "${BLUE}Running standalone load tests...${NC}"
            echo -e "\n${YELLOW}=== 50 Users ===${NC}"
            python tests/load_test_concurrency.py 50
            
            echo -e "\n${YELLOW}=== 100 Users ===${NC}"
            python tests/load_test_concurrency.py 100
            
            echo -e "\n${YELLOW}=== 200 Users (Stress) ===${NC}"
            python tests/load_test_concurrency.py 200
            ;;
        
        *)
            echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Main execution
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}FYJC Bot Test Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Test Type: ${GREEN}$TEST_TYPE${NC}"
echo -e "Server URL: ${GREEN}$URL${NC}"
echo -e "Verbosity: ${GREEN}$VERBOSITY${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Check server (except for help)
if [ "$TEST_TYPE" != "help" ]; then
    if ! check_server; then
        exit 1
    fi
fi

# Run tests
run_tests

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${GREEN}======================================${NC}"
