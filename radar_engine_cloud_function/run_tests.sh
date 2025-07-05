#!/bin/bash

# Test runner script for Radar Scanner
echo "🧪 Radar Scanner Test Runner"
echo "============================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_testing_env.sh first."
    exit 1
fi

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Parse command line arguments
TEST_TYPE=${1:-"all"}
SYMBOL=${2:-"RELIANCE"}
SCENARIO=${3:-"SIDEWAYS"}

echo "🔧 Test Configuration:"
echo "   Test Type: $TEST_TYPE"
echo "   Symbol: $SYMBOL"
echo "   Scenario: $SCENARIO"
echo ""

# Run the appropriate test
case $TEST_TYPE in
    "all")
        echo "🚀 Running comprehensive test suite..."
        python quick_test_runner.py --test all
        ;;
    "alert")
        echo "🔍 Testing alert detection..."
        python quick_test_runner.py --test alert --symbol $SYMBOL
        ;;
    "strategy")
        echo "📈 Testing strategy performance..."
        python quick_test_runner.py --test strategy --symbol $SYMBOL --scenario $SCENARIO
        ;;
    "indicator")
        echo "📊 Testing indicator calculations..."
        python quick_test_runner.py --test indicator --symbol $SYMBOL
        ;;
    "data")
        echo "🔍 Testing data quality..."
        python quick_test_runner.py --test data
        ;;
    "dashboard")
        echo "🖥️  Launching development dashboard..."
        python development_dashboard.py
        ;;
    "comprehensive")
        echo "📋 Running comprehensive scanner tests..."
        python scanner_tester.py
        ;;
    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Available options: all, alert, strategy, indicator, data, dashboard, comprehensive"
        exit 1
        ;;
esac

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tests completed successfully!"
else
    echo ""
    echo "❌ Tests failed. Check the output above for details."
    exit 1
fi 