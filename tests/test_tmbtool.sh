#!/bin/bash

# Integration tests for tmbtool.sh
# ================================

# Load the testing framework
TEST_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$TEST_DIR/test_framework.sh"

# Setup test environment
PROJECT_ROOT="$(dirname "$TEST_DIR")"
TMBTOOL_SCRIPT="$PROJECT_ROOT/tmbtool.sh"

test_suite "TMBTool Integration Tests"

# Test script existence and permissions
test_case "tmbtool.sh exists and is executable"
assert_file_exists "$TMBTOOL_SCRIPT"

test_case "tmbtool.sh has execute permissions"
if [[ -x "$TMBTOOL_SCRIPT" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
fi
TEST_COUNT=$((TEST_COUNT + 1))

# Test help functionality
test_case "tmbtool.sh --help displays help"
output=$(cd "$PROJECT_ROOT" && timeout 10 ./tmbtool.sh --help 2>&1)
exit_code=$?
assert_equals "0" "$exit_code"
assert_contains "$output" "TheOpenMusicBox Unified Tool"
assert_contains "$output" "GETTING STARTED"

test_case "tmbtool.sh -h displays help"
output=$(cd "$PROJECT_ROOT" && timeout 10 ./tmbtool.sh -h 2>&1)
exit_code=$?
assert_equals "0" "$exit_code"
assert_contains "$output" "USAGE:"

# Test version information
test_case "tmbtool.sh help contains version"
output=$(cd "$PROJECT_ROOT" && timeout 10 ./tmbtool.sh --help 2>&1)
assert_contains "$output" "v2.0.0"

# Test command recognition
test_case "tmbtool.sh recognizes config command"
output=$(cd "$PROJECT_ROOT" && echo | timeout 5 ./tmbtool.sh config 2>&1 || true)
assert_contains "$output" "Configuration Setup"

test_case "tmbtool.sh recognizes ssh-setup command"
output=$(cd "$PROJECT_ROOT" && echo | timeout 5 ./tmbtool.sh ssh-setup 2>&1 || true)
assert_contains "$output" "SSH Setup"

test_case "tmbtool.sh recognizes deploy command"
output=$(cd "$PROJECT_ROOT" && echo | timeout 5 ./tmbtool.sh deploy 2>&1 || true)
# Should either show deploy menu or error about missing config
if [[ "$output" == *"Deploy Application"* ]] || [[ "$output" == *"Server not configured"* ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
    printf "  ${T_RED}Output:${T_NC} %s\n" "$output"
fi
TEST_COUNT=$((TEST_COUNT + 1))

test_case "tmbtool.sh recognizes test command"
output=$(cd "$PROJECT_ROOT" && echo | timeout 5 ./tmbtool.sh test 2>&1 || true)
assert_contains "$output" "Run Tests"

# Test error handling
test_case "tmbtool.sh handles unknown command gracefully"
output=$(cd "$PROJECT_ROOT" && timeout 5 ./tmbtool.sh unknown-command 2>&1)
exit_code=$?
assert_equals "1" "$exit_code"
assert_contains "$output" "Unknown command"

# Test legacy command compatibility
test_case "tmbtool.sh supports --prod command"
output=$(cd "$PROJECT_ROOT" && echo | timeout 5 ./tmbtool.sh --prod 2>&1 || true)
# Should either show deploy menu or error about missing config
if [[ "$output" == *"Deploy Application"* ]] || [[ "$output" == *"Server not configured"* ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
fi
TEST_COUNT=$((TEST_COUNT + 1))

test_case "tmbtool.sh supports --test-only command"
output=$(cd "$PROJECT_ROOT" && echo | timeout 5 ./tmbtool.sh --test-only 2>&1 || true)
assert_contains "$output" "Run Tests"

test_case "tmbtool.sh supports --monitor command"
output=$(cd "$PROJECT_ROOT" && timeout 5 ./tmbtool.sh --monitor 2>&1 || true)
exit_code=$?
# Should exit with error since SSH not configured
assert_equals "1" "$exit_code"
assert_contains "$output" "SSH not configured"

# Test module loading
test_suite "Module Loading Tests"

test_case "tmbtool.sh loads all required modules"
# Check that all module files exist
for module in "utils.sh" "config.sh" "ssh.sh" "setup.sh" "deploy.sh"; do
    module_path="$PROJECT_ROOT/tmbtool/$module"
    if [[ ! -f "$module_path" ]]; then
        FAIL_COUNT=$((FAIL_COUNT + 1))
        printf "${T_RED}✗${T_NC} Missing module: %s\n" "$module"
        TEST_COUNT=$((TEST_COUNT + 1))
        continue
    fi
done
PASS_COUNT=$((PASS_COUNT + 1))
printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
TEST_COUNT=$((TEST_COUNT + 1))

test_case "tmbtool.sh handles missing module gracefully"
# Temporarily rename a module to test error handling
mv "$PROJECT_ROOT/tmbtool/utils.sh" "$PROJECT_ROOT/tmbtool/utils.sh.backup" 2>/dev/null || true
output=$(cd "$PROJECT_ROOT" && timeout 5 ./tmbtool.sh --help 2>&1 || true)
exit_code=$?
# Restore the module
mv "$PROJECT_ROOT/tmbtool/utils.sh.backup" "$PROJECT_ROOT/tmbtool/utils.sh" 2>/dev/null || true

assert_equals "1" "$exit_code"
assert_contains "$output" "Required file"

# Test configuration handling
test_suite "Configuration Tests"

test_case "tmbtool.sh handles missing configuration gracefully"
output=$(cd "$PROJECT_ROOT" && timeout 10 ./tmbtool.sh --help 2>&1)
# Should show warning about missing config but still work
assert_contains "$output" "No configuration file found"
assert_contains "$output" "USAGE:"

# Test interactive menu (limited testing due to interactivity)
test_suite "Interactive Menu Tests"

test_case "tmbtool.sh shows main menu when run without arguments"
output=$(cd "$PROJECT_ROOT" && echo "0" | timeout 10 ./tmbtool.sh 2>&1)
assert_contains "$output" "Main Menu"
assert_contains "$output" "Configuration"
assert_contains "$output" "SSH Tool"
assert_contains "$output" "Setup"
assert_contains "$output" "Deploy"
assert_contains "$output" "Tests"

test_case "tmbtool.sh exits gracefully from main menu"
output=$(cd "$PROJECT_ROOT" && echo "0" | timeout 10 ./tmbtool.sh 2>&1)
assert_contains "$output" "Goodbye"

# Test script syntax
test_suite "Syntax and Style Tests"

test_case "tmbtool.sh has valid bash syntax"
output=$(bash -n "$TMBTOOL_SCRIPT" 2>&1)
exit_code=$?
assert_equals "0" "$exit_code"

test_case "All module files have valid bash syntax"
for module in "$PROJECT_ROOT/tmbtool"/*.sh; do
    if [[ -f "$module" ]]; then
        output=$(bash -n "$module" 2>&1)
        exit_code=$?
        if [[ $exit_code -ne 0 ]]; then
            FAIL_COUNT=$((FAIL_COUNT + 1))
            printf "${T_RED}✗${T_NC} Syntax error in: %s\n" "$(basename "$module")"
            printf "  ${T_RED}Error:${T_NC} %s\n" "$output"
            TEST_COUNT=$((TEST_COUNT + 1))
            continue
        fi
    fi
done
PASS_COUNT=$((PASS_COUNT + 1))
printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
TEST_COUNT=$((TEST_COUNT + 1))

# Performance tests
test_suite "Performance Tests"

test_case "tmbtool.sh loads quickly"
start_time=$(date +%s%N)
output=$(cd "$PROJECT_ROOT" && timeout 10 ./tmbtool.sh --help 2>&1)
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds

# Should load and show help in under 2000ms
if [[ $duration -lt 2000 ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf "${T_GREEN}✓${T_NC} %s (${duration}ms)\n" "$CURRENT_TEST"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf "${T_RED}✗${T_NC} %s (${duration}ms - too slow)\n" "$CURRENT_TEST"
fi
TEST_COUNT=$((TEST_COUNT + 1))

# Security tests
test_suite "Security Tests"

test_case "tmbtool.sh doesn't expose sensitive information in help"
output=$(cd "$PROJECT_ROOT" && timeout 10 ./tmbtool.sh --help 2>&1)
# Check that no passwords, keys, or sensitive data is exposed
if echo "$output" | grep -qi "password\|secret\|key\|token"; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
    printf "  ${T_RED}Potentially sensitive information found in help output${T_NC}\n"
else
    PASS_COUNT=$((PASS_COUNT + 1))
    printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
fi
TEST_COUNT=$((TEST_COUNT + 1))

test_case "tmbtool.sh doesn't execute arbitrary commands"
# Test that special characters don't cause command injection
output=$(cd "$PROJECT_ROOT" && timeout 5 ./tmbtool.sh '; echo "INJECTED"' 2>&1 || true)
if echo "$output" | grep -q "INJECTED"; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf "${T_RED}✗${T_NC} %s\n" "$CURRENT_TEST"
    printf "  ${T_RED}Possible command injection vulnerability${T_NC}\n"
else
    PASS_COUNT=$((PASS_COUNT + 1))
    printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
fi
TEST_COUNT=$((TEST_COUNT + 1))