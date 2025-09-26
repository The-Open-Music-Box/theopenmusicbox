#!/bin/bash

# Tests for tmbtool/utils.sh
# ==========================

# Load the testing framework
TEST_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$TEST_DIR/test_framework.sh"

# Load the module under test
PROJECT_ROOT="$(dirname "$TEST_DIR")"
source "$PROJECT_ROOT/tmbtool/utils.sh"

test_suite "Utils Module Tests"

# Test validate_input function
test_case "validate_input accepts valid hostname"
setup() {
    # Redirect stderr to suppress error messages during testing
    exec 3>&2 2>/dev/null
}
teardown() {
    # Restore stderr
    exec 2>&3 3>&-
}

setup
result=$(validate_input "example.com" "hostname" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"

test_case "validate_input accepts hostname with underscores"
setup
result=$(validate_input "test_server.local" "hostname" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"

test_case "validate_input rejects hostname with invalid characters"
setup
result=$(validate_input "test@server.com" "hostname" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "invalid" "$result"

test_case "validate_input accepts valid username"
setup
result=$(validate_input "admin" "username" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"

test_case "validate_input accepts username with underscore"
setup
result=$(validate_input "test_user" "username" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"

test_case "validate_input rejects username with invalid characters"
setup
result=$(validate_input "user@domain" "username" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "invalid" "$result"

test_case "validate_input accepts valid path"
setup
result=$(validate_input "/home/admin/tomb" "path" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"

test_case "validate_input accepts relative path"
setup
result=$(validate_input "./local/path" "path" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"

test_case "validate_input accepts valid SSH alias"
setup
result=$(validate_input "tomb-server" "alias" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"

test_case "validate_input rejects alias with invalid characters"
setup
result=$(validate_input "alias@server" "alias" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "invalid" "$result"

# Test print_status function (test that it doesn't crash)
test_case "print_status outputs colored text"
output=$(print_status "$GREEN" "Test message" 2>&1)
assert_contains "$output" "Test message"

test_case "print_header outputs formatted header"
output=$(print_header "Test Header" 2>&1)
assert_contains "$output" "Test Header"

# Test configuration functions
test_case "save_config creates configuration file"
# Create a temporary config file for testing
TEST_CONFIG_FILE="/tmp/test_tmbtool.config"
CONFIG_FILE="$TEST_CONFIG_FILE"
REMOTE_HOST="test.example.com"
REMOTE_USER="testuser"
REMOTE_DIR="/test/dir"
SSH_ALIAS="test-alias"
REPO_URL="https://github.com/test/repo"

save_config >/dev/null 2>&1
assert_file_exists "$TEST_CONFIG_FILE"

test_case "load_config reads configuration file"
# Test loading the config we just created
CONFIG_FILE="$TEST_CONFIG_FILE"
REMOTE_HOST=""  # Reset to test loading
load_config >/dev/null 2>&1
assert_equals "test.example.com" "$REMOTE_HOST"

# Cleanup
rm -f "$TEST_CONFIG_FILE" 2>/dev/null

# Test cases for edge cases and error conditions
test_suite "Edge Cases and Error Handling"

test_case "validate_input handles empty input"
setup
result=$(validate_input "" "hostname" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "invalid" "$result"

test_case "validate_input handles unknown type"
setup
result=$(validate_input "test" "unknown_type" 2>/dev/null && echo "valid" || echo "invalid")
teardown
assert_equals "valid" "$result"  # Should pass through unknown types

test_case "load_config handles missing file gracefully"
CONFIG_FILE="/nonexistent/file"
setup
result=$(load_config 2>/dev/null && echo "success" || echo "failure")
teardown
assert_equals "failure" "$result"

# Performance tests
test_suite "Performance Tests"

test_case "validate_input performs quickly on valid input"
start_time=$(date +%s%N)
for i in {1..100}; do
    validate_input "test.example.com" "hostname" >/dev/null 2>&1
done
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds

# Should complete 100 validations in under 1000ms (very generous)
if [[ $duration -lt 1000 ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf "${T_GREEN}✓${T_NC} %s (${duration}ms)\n" "$CURRENT_TEST"
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf "${T_RED}✗${T_NC} %s (${duration}ms - too slow)\n" "$CURRENT_TEST"
fi
TEST_COUNT=$((TEST_COUNT + 1))

# Test real-world scenarios
test_suite "Real-world Scenarios"

test_case "validate_input accepts common hostnames"
for hostname in "localhost" "raspberrypi.local" "192.168.1.100" "tmbdev.local" "server-01.example.com"; do
    setup
    result=$(validate_input "$hostname" "hostname" 2>/dev/null && echo "valid" || echo "invalid")
    teardown
    if [[ "$result" != "valid" ]]; then
        printf "${T_RED}✗${T_NC} Failed for hostname: %s\n" "$hostname"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        TEST_COUNT=$((TEST_COUNT + 1))
        continue
    fi
done
printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
PASS_COUNT=$((PASS_COUNT + 1))
TEST_COUNT=$((TEST_COUNT + 1))

test_case "validate_input accepts common usernames"
for username in "pi" "admin" "root" "ubuntu" "test_user" "user-123"; do
    setup
    result=$(validate_input "$username" "username" 2>/dev/null && echo "valid" || echo "invalid")
    teardown
    if [[ "$result" != "valid" ]]; then
        printf "${T_RED}✗${T_NC} Failed for username: %s\n" "$username"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        TEST_COUNT=$((TEST_COUNT + 1))
        continue
    fi
done
printf "${T_GREEN}✓${T_NC} %s\n" "$CURRENT_TEST"
PASS_COUNT=$((PASS_COUNT + 1))
TEST_COUNT=$((TEST_COUNT + 1))