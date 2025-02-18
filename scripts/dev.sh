#!/bin/bash

# Function to display help message
show_help() {
    echo "Blackprint Development Helper Script"
    echo
    echo "Usage: ./dev.sh [command]"
    echo
    echo "Commands:"
    echo "  up        Start development container"
    echo "  down      Stop development container"
    echo "  shell     Open shell in development container"
    echo "  test      Run test suite"
    echo "  format    Format code with black"
    echo "  lint      Run linter checks"
    echo "  clean     Clean up development environment"
    echo "  help      Show this help message"
}

# Function to start development environment
start_dev() {
    docker-compose -f docker-compose.dev.yml up -d
    echo "Development environment started"
    echo "Run './dev.sh shell' to enter the container"
}

# Function to stop development environment
stop_dev() {
    docker-compose -f docker-compose.dev.yml down
    echo "Development environment stopped"
}

# Function to open shell in development container
open_shell() {
    docker exec -it blackprint-dev bash
}

# Function to run tests
run_tests() {
    docker exec blackprint-dev pytest -v
}

# Function to format code
format_code() {
    docker exec blackprint-dev black .
}

# Function to run linter
run_lint() {
    docker exec blackprint-dev flake8 .
}

# Function to clean up
cleanup() {
    docker-compose -f docker-compose.dev.yml down -v
    echo "Development environment cleaned"
}

# Main script logic
case "$1" in
    "up")
        start_dev
        ;;
    "down")
        stop_dev
        ;;
    "shell")
        open_shell
        ;;
    "test")
        run_tests
        ;;
    "format")
        format_code
        ;;
    "lint")
        run_lint
        ;;
    "clean")
        cleanup
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run './dev.sh help' for usage information"
        exit 1
        ;;
esac
