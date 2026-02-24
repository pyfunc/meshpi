#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# End-to-End RPi Architecture Test Runner
#
# This script runs comprehensive tests of MeshPi installation across
# different Raspberry Pi architectures using Docker.
#
# Usage:
#   ./run-rpi-tests.sh                    # Test all architectures
#   ./run-rpi-tests.sh --arch arm32v6     # Test specific architecture
#   ./run-rpi-tests.sh --quick            # Quick test (no builds)
#   ./run-rpi-tests.sh --clean            # Clean and rebuild
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_DIR/test-results"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.test-rpi.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default arguments
ARCH_FILTER=""
QUICK_MODE=false
CLEAN_BUILD=false
VERBOSE=false
PARALLEL=true

# Help function
show_help() {
    cat << EOF
RPi Architecture Test Runner

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --arch ARCH         Test specific architecture (arm32v6, arm32v7, arm64v8)
    --quick              Skip Docker builds, use existing images
    --clean              Clean existing images before building
    --verbose            Verbose output
    --sequential         Run tests sequentially (not parallel)
    --help               Show this help

EXAMPLES:
    $0                           # Test all architectures
    $0 --arch arm32v6            # Test only arm32v6 (RPi Zero)
    $0 --quick                   # Quick test with existing images
    $0 --clean --arch arm64v8    # Clean build for arm64v8 only

EOF
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --arch)
                ARCH_FILTER="$2"
                shift 2
                ;;
            --quick)
                QUICK_MODE=true
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --sequential)
                PARALLEL=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if we can run multi-architecture builds
    if ! docker buildx version &> /dev/null; then
        log_warning "Docker Buildx not available, multi-architecture builds may fail"
    fi
    
    # Create results directory
    mkdir -p "$RESULTS_DIR"
    
    log_success "Prerequisites check passed"
}

# Clean existing images and containers
clean_environment() {
    log_info "Cleaning existing test environment..."
    
    # Stop and remove test containers
    if docker-compose -f "$COMPOSE_FILE" ps -q 2>/dev/null | grep -q .; then
        log_info "Stopping existing test containers..."
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true
    fi
    
    if [[ "$CLEAN_BUILD" == "true" ]]; then
        log_info "Removing existing test images..."
        docker images --format "table {{.Repository}}:{{.Tag}}" | grep "meshpi-test-" | tail -n +2 | while read -r image; do
            if [[ -n "$image" ]]; then
                docker rmi "$image" 2>/dev/null || true
            fi
        done
    fi
    
    # Clean old results
    find "$RESULTS_DIR" -name "meshpi-test-*.json" -mtime +7 -delete 2>/dev/null || true
    
    log_success "Environment cleaned"
}

# Build Docker images
build_images() {
    if [[ "$QUICK_MODE" == "true" ]]; then
        log_info "Skipping Docker builds (quick mode)"
        return
    fi
    
    log_info "Building Docker images for RPi architectures..."
    
    local compose_args=""
    if [[ "$VERBOSE" == "true" ]]; then
        compose_args="--verbose"
    fi
    
    # Build specific architecture if filter is set
    if [[ -n "$ARCH_FILTER" ]]; then
        local service_name="meshpi-test-$ARCH_FILTER"
        log_info "Building image for architecture: $ARCH_FILTER"
        docker-compose -f "$COMPOSE_FILE" build $compose_args "$service_name"
    else
        log_info "Building all architecture images..."
        docker-compose -f "$COMPOSE_FILE" build $compose_args
    fi
    
    log_success "Docker images built successfully"
}

# Run tests
run_tests() {
    log_info "Running MeshPi installation tests..."
    
    local compose_args=""
    if [[ "$PARALLEL" == "false" ]]; then
        compose_args="--no-parallel"
    fi
    
    # Set up environment variables
    export MESHPI_TEST_TIMESTAMP=$(date +%s)
    export MESHPI_TEST_RUNNER="end-to-end"
    
    # Run specific architecture or all
    if [[ -n "$ARCH_FILTER" ]]; then
        local service_name="meshpi-test-$ARCH_FILTER"
        log_info "Running tests for architecture: $ARCH_FILTER"
        
        if docker-compose -f "$COMPOSE_FILE" run --rm $compose_args "$service_name"; then
            log_success "Tests completed for $ARCH_FILTER"
        else
            log_error "Tests failed for $ARCH_FILTER"
            return 1
        fi
    else
        log_info "Running tests for all architectures..."
        
        if docker-compose -f "$COMPOSE_FILE" up --abort-on-container-exit $compose_args; then
            log_success "All tests completed successfully"
        else
            log_error "Some tests failed"
            return 1
        fi
    fi
}

# Aggregate results
aggregate_results() {
    log_info "Aggregating test results..."
    
    # Run the aggregator container
    if docker-compose -f "$COMPOSE_FILE" --profile aggregate run --rm meshpi-test-aggregator; then
        log_success "Results aggregated successfully"
        
        # Show summary if available
        local summary_file="$RESULTS_DIR/test-summary.json"
        if [[ -f "$summary_file" ]]; then
            log_info "Test summary available at: $summary_file"
            
            # Extract key metrics
            if command -v jq &> /dev/null; then
                local overall_status=$(jq -r '.overall_status' "$summary_file")
                local total_tests=$(jq -r '.total_tests' "$summary_file")
                log_info "Overall Status: $overall_status"
                log_info "Total Tests: $total_tests"
            fi
        fi
    else
        log_warning "Results aggregation failed"
    fi
}

# Generate report
generate_report() {
    log_info "Generating test report..."
    
    local report_file="$RESULTS_DIR/test-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# MeshPi RPi Architecture Test Report

**Generated:** $(date)
**Test Runner:** End-to-End Test Suite

## Test Configuration

EOF
    
    if [[ -n "$ARCH_FILTER" ]]; then
        echo "**Architecture Filter:** $ARCH_FILTER" >> "$report_file"
    else
        echo "**Architectures:** All (arm32v6, arm32v7, arm64v8)" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

**Quick Mode:** $QUICK_MODE
**Clean Build:** $CLEAN_BUILD
**Parallel Execution:** $PARALLEL

## Results Summary

EOF
    
    # Add results if available
    local summary_file="$RESULTS_DIR/test-summary.json"
    if [[ -f "$summary_file" ]]; then
        if command -v jq &> /dev/null; then
            jq -r '.architectures | to_entries[] | 
"### \(.key | ascii_upcase)\n\n- **Architecture:** \(.value.architecture)\n- **Model:** \(.value.model)\n- **Python Version:** \(.value.python_version)\n- **Status:** \(.value.status)\n- **Tests Passed:** \(.value.passed)\n- **Tests Failed:** \(.value.failed)\n"' \
            "$summary_file" >> "$report_file"
        fi
    fi
    
    cat >> "$report_file" << EOF

## Test Files

Individual test results are available in JSON format:
EOF
    
    ls -la "$RESULTS_DIR"/meshpi-test-*.json 2>/dev/null | awk '{print "- " $9}' >> "$report_file" || true
    
    log_success "Test report generated: $report_file"
}

# Main execution
main() {
    log_info "Starting MeshPi RPi Architecture Test Suite"
    
    parse_args "$@"
    check_prerequisites
    clean_environment
    build_images
    
    if run_tests; then
        aggregate_results
        generate_report
        log_success "Test suite completed successfully"
    else
        log_error "Test suite failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
