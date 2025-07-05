#!/bin/bash

# Simple script to activate the virtual environment
echo "🚀 Activating Radar Scanner Virtual Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup_testing_env.sh first to create the environment."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"
echo ""
echo "🎯 You can now run:"
echo "   python quick_test_runner.py"
echo "   python development_dashboard.py"
echo "   python scanner_tester.py"
echo ""
echo "💡 To deactivate, run: deactivate" 