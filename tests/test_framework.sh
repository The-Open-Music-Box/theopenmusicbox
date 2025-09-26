#!/bin/bash

# TMBTool Testing Framework
# =========================
# Lightweight testing framework for shell scripts

# Test counters
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0
CURRENT_TEST=""

# Colors for output
readonly T_RED='\033[0;31m'
readonly T_GREEN='\033[0;32m'
readonly T_YELLOW='\033[1;33m'
readonly T_BLUE='\033[0;34m'
readonly T_BOLD='\033[1m'
readonly T_NC='\033[0m'

# Test assertion functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"

    TEST_COUNT=$((TEST_COUNT + 1))

    if [[ "$expected" == "$actual" ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
        [[ -n "$message" ]] && printf "  %s\n" "$message"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
        printf "  ${T_RED}Expected:${T_NC} '%s'\n" "$expected"
        printf "  ${T_RED}Actual:${T_NC}   '%s'\n" "$actual"
        [[ -n "$message" ]] && printf "  ${T_RED}Message:${T_NC}  %s\n" "$message"
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"

    TEST_COUNT=$((TEST_COUNT + 1))

    if [[ "$haystack" == *"$needle"* ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
        [[ -n "$message" ]] && printf "  %s\n" "$message"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
        printf "  ${T_RED}Haystack:${T_NC} '%s'\n" "$haystack"
        printf "  ${T_RED}Needle:${T_NC}   '%s'\n" "$needle"
        [[ -n "$message" ]] && printf "  ${T_RED}Message:${T_NC}  %s\n" "$message"
    fi
}

assert_exit_code() {
    local expected_code="$1"
    local command="$2"
    local message="${3:-}"

    TEST_COUNT=$((TEST_COUNT + 1))

    # Run command and capture exit code
    eval "$command" >/dev/null 2>&1
    local actual_code=$?

    if [[ "$expected_code" -eq "$actual_code" ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
        [[ -n "$message" ]] && printf "  %s\n" "$message"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
        printf "  ${T_RED}Expected exit code:${T_NC} %d\n" "$expected_code"
        printf "  ${T_RED}Actual exit code:${T_NC}   %d\n" "$actual_code"
        [[ -n "$message" ]] && printf "  ${T_RED}Message:${T_NC} %s\n" "$message"
    fi
}

assert_file_exists() {
    local file="$1"
    local message="${2:-}"

    TEST_COUNT=$((TEST_COUNT + 1))

    if [[ -f "$file" ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
        [[ -n "$message" ]] && printf "  %s\n" "$message"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
        printf "  ${T_RED}File not found:${T_NC} %s\n" "$file"
        [[ -n "$message" ]] && printf "  ${T_RED}Message:${T_NC} %s\n" "$message"
    fi
}

# Test organization functions
test_suite() {
    local suite_name="$1"
    printf "\n${T_BLUE}${T_BOLD}=== %s ===${T_NC}\n" "$suite_name"
}

test_case() {
    CURRENT_TEST="$1"
}

# Test setup and teardown
setup() {
    # Override in test files if needed
    :
}

teardown() {
    # Override in test files if needed
    :
}

# Test runner
run_test_file() {
    local test_file="$1"

    if [[ ! -f "$test_file" ]]; then
        printf "${T_RED}Test file not found: %s${T_NC}\n" "$test_file"
        return 1
    fi

    printf "${T_YELLOW}Running tests from: %s${T_NC}\n" "$(basename "$test_file")"

    # Source the test file
    source "$test_file"
}

# Summary
show_summary() {
    printf "\n${T_BOLD}=== Test Summary ===${T_NC}\n"
    printf "Total tests: %d\n" "$TEST_COUNT"
    printf "${T_GREEN}Passed: %d${T_NC}\n" "$PASS_COUNT"

    if [[ "$FAIL_COUNT" -gt 0 ]]; then
        printf "${T_RED}Failed: %d${T_NC}\n" "$FAIL_COUNT"
        return 1
    else
        printf "${T_GREEN}All tests passed!${T_NC}\n"
        return 0
    fi
}

# Helper function to run command and capture output
run_command() {
    local command="$1"
    eval "$command" 2>&1
}

# Mock functions for testing
mock_function() {
    local func_name="$1"
    local return_value="${2:-0}"
    local output="${3:-}"

    eval "${func_name}() {
        [[ -n \"$output\" ]] && echo \"$output\"
        return $return_value
    }"
}