#!/bin/bash

# TMBTool Test Runner
# ==================
# Comprehensive test runner for all tmbtool components

set -e

# Test runner metadata
readonly TEST_RUNNER_VERSION="1.0.0"
readonly TEST_RUNNER_NAME="TMBTool Test Runner"

# Colors for output
readonly T_RED='\033[0;31m'
readonly T_GREEN='\033[0;32m'
readonly T_YELLOW='\033[1;33m'
readonly T_BLUE='\033[0;34m'
readonly T_BOLD='\033[1m'
readonly T_NC='\033[0m'

# Test directories and files
TEST_DIR="$(dirname "${BASH_SOURCE[0]}")"
PROJECT_ROOT="$(dirname "$TEST_DIR")"

# Test statistics
TOTAL_TEST_FILES=0
PASSED_TEST_FILES=0
FAILED_TEST_FILES=0

# Functions
print_header() {
    printf "\n${T_BLUE}${T_BOLD}%s${T_NC}\n" "$1"
    local line_length=${#1}
    printf "${T_BLUE}"
    for ((i=0; i<line_length; i++)); do printf "="; done
    printf "${T_NC}\n"
}

print_status() {
    local color="$1"
    local message="$2"
    printf "${color}%s${T_NC}\n" "$message"
}

run_test_file() {
    local test_file="$1"
    local test_name="$(basename "$test_file" .sh)"

    printf "\n${T_YELLOW}Running: %s${T_NC}\n" "$test_name"
    printf "${T_YELLOW}"
    for ((i=0; i<40; i++)); do printf "-"; done
    printf "${T_NC}\n"

    TOTAL_TEST_FILES=$((TOTAL_TEST_FILES + 1))

    # Run the test file and capture results
    if bash "$test_file"; then
        PASSED_TEST_FILES=$((PASSED_TEST_FILES + 1))
        print_status "$T_GREEN" "✓ $test_name completed successfully"
    else
        FAILED_TEST_FILES=$((FAILED_TEST_FILES + 1))
        print_status "$T_RED" "✗ $test_name failed"
    fi
}

run_all_tests() {
    print_header "$TEST_RUNNER_NAME v$TEST_RUNNER_VERSION"

    # Find all test files
    local test_files=()
    while IFS= read -r -d '' file; do
        test_files+=("$file")
    done < <(find "$TEST_DIR" -name "test_*.sh" -type f -print0 | sort -z)

    if [[ ${#test_files[@]} -eq 0 ]]; then
        print_status "$T_YELLOW" "⚠️  No test files found in $TEST_DIR"
        exit 0
    fi

    print_status "$T_BLUE" "📋 Found ${#test_files[@]} test file(s)"

    # Run each test file
    for test_file in "${test_files[@]}"; do
        run_test_file "$test_file"
    done
}

show_summary() {
    print_header "Test Summary"

    printf "Test Files: %d\n" "$TOTAL_TEST_FILES"
    printf "${T_GREEN}Passed Files: %d${T_NC}\n" "$PASSED_TEST_FILES"

    if [[ "$FAILED_TEST_FILES" -gt 0 ]]; then
        printf "${T_RED}Failed Files: %d${T_NC}\n" "$FAILED_TEST_FILES"
    fi

    # Overall result
    printf "\n"
    if [[ "$FAILED_TEST_FILES" -eq 0 ]]; then
        print_status "$T_GREEN" "🎉 All test files passed!"
        return 0
    else
        print_status "$T_RED" "❌ Some test files failed"
        return 1
    fi
}

show_help() {
    echo -e "${T_BOLD}$TEST_RUNNER_NAME v$TEST_RUNNER_VERSION${T_NC}"
    echo "======================================"
    echo ""
    echo -e "${T_BOLD}DESCRIPTION:${T_NC}"
    echo "  Runs all test files in the tests directory and provides a comprehensive summary."
    echo ""
    echo -e "${T_BOLD}USAGE:${T_NC}"
    echo "  $0 [OPTIONS]"
    echo ""
    echo -e "${T_BOLD}OPTIONS:${T_NC}"
    echo "  -h, --help      Show this help message"
    echo "  -v, --verbose   Enable verbose output"
    echo "  -q, --quiet     Enable quiet mode (minimal output)"
    echo "  --list          List all available test files"
    echo ""
    echo -e "${T_BOLD}EXAMPLES:${T_NC}"
    echo "  $0              # Run all tests"
    echo "  $0 --list       # Show available test files"
    echo "  $0 --verbose    # Run tests with detailed output"
    echo ""
    echo -e "${T_BOLD}TEST FILES:${T_NC}"
    echo "  Tests are automatically discovered in the tests/ directory."
    echo "  All files matching the pattern 'test_*.sh' will be executed."
    echo ""
}

list_test_files() {
    print_header "Available Test Files"

    local test_files=()
    while IFS= read -r -d '' file; do
        test_files+=("$file")
    done < <(find "$TEST_DIR" -name "test_*.sh" -type f -print0 | sort -z)

    if [[ ${#test_files[@]} -eq 0 ]]; then
        print_status "$T_YELLOW" "⚠️  No test files found in $TEST_DIR"
        return
    fi

    for test_file in "${test_files[@]}"; do
        local test_name="$(basename "$test_file" .sh)"
        local relative_path="${test_file#$PROJECT_ROOT/}"
        printf "  %s (%s)\n" "$test_name" "$relative_path"
    done

    printf "\nTotal: %d test file(s)\n" "${#test_files[@]}"
}

# Argument parsing
VERBOSE=false
QUIET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        --list)
            list_test_files
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate test environment
if [[ ! -f "$TEST_DIR/test_framework.sh" ]]; then
    print_status "$T_RED" "❌ Test framework not found: $TEST_DIR/test_framework.sh"
    exit 1
fi

if [[ ! -f "$PROJECT_ROOT/tmbtool.sh" ]]; then
    print_status "$T_RED" "❌ Main script not found: $PROJECT_ROOT/tmbtool.sh"
    exit 1
fi

# Change to project root for consistent relative paths
cd "$PROJECT_ROOT"

# Run tests and show summary
if ! $QUIET; then
    run_all_tests
    exit_code=0
    show_summary || exit_code=$?
    exit $exit_code
else
    # Quiet mode - run tests with minimal output
    run_all_tests >/dev/null 2>&1
    if [[ "$FAILED_TEST_FILES" -eq 0 ]]; then
        echo "All test files passed ($PASSED_TEST_FILES/$TOTAL_TEST_FILES)"
        exit 0
    else
        echo "Test files failed ($PASSED_TEST_FILES/$TOTAL_TEST_FILES passed)"
        exit 1
    fi
fi