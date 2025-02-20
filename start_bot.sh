#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Determine Python command
if command_exists python3; then
    PYTHON_CMD=python3
elif command_exists python; then
    PYTHON_CMD=python
else
    echo "Error: Neither python3 nor python found in PATH!"
    echo "Please install Python 3.10 or later"
    exit 1
fi

# Check Python version
$PYTHON_CMD -c "import sys; sys.exit(0) if sys.version_info >= (3,10) else (print('Error: Python 3.10 or later required!') or sys.exit(1))"
if [ $? -ne 0 ]; then
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found!"
    echo "Creating new virtual environment..."
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy env.example to .env and configure your settings"
    exit 1
fi

echo "Starting Blackprint Trading Bot..."
$PYTHON_CMD -m bot.main
